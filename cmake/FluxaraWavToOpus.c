/*
 * Tiny host-side WAV (16-bit PCM) -> Ogg/Opus writer for Fluxara iOS
 * packaging.  It deliberately has no runtime role and keeps audio conversion
 * independent from a system ffmpeg installation.
 */
#include <errno.h>
#include <ogg/ogg.h>
#include <opus.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint16_t le16(const unsigned char *p)
{
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static uint32_t le32(const unsigned char *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int write_pages(FILE *output, ogg_stream_state *stream, int flush)
{
    ogg_page page;
    int result;
    while ((result = flush ? ogg_stream_flush(stream, &page)
                           : ogg_stream_pageout(stream, &page)) != 0)
    {
        if (fwrite(page.header, 1, (size_t)page.header_len, output) != (size_t)page.header_len ||
            fwrite(page.body, 1, (size_t)page.body_len, output) != (size_t)page.body_len)
            return 0;
    }
    return 1;
}

static int packet_in(FILE *output, ogg_stream_state *stream, unsigned char *data,
                     long bytes, ogg_int64_t granulepos, int eos, int flush)
{
    ogg_packet packet;
    memset(&packet, 0, sizeof(packet));
    packet.packet = data;
    packet.bytes = bytes;
    packet.granulepos = granulepos;
    packet.e_o_s = eos;
    if (ogg_stream_packetin(stream, &packet) != 0)
        return 0;
    return write_pages(output, stream, flush);
}

int main(int argc, char **argv)
{
    FILE *input = NULL, *output = NULL;
    unsigned char header[12], chunk[8], *pcm_bytes = NULL;
    int16_t *pcm = NULL;
    uint32_t pcm_size = 0, sample_rate = 0, total_frames = 0;
    uint16_t format = 0, channels = 0, bits = 0;
    int bitrate, opus_error, pre_skip = 0, frame = 960;
    OpusEncoder *encoder = NULL;
    ogg_stream_state stream;
    unsigned char opus_head[19], opus_tags[20], encoded[4000];
    uint32_t position = 0;
    int success = 0;

    if (argc != 4 || (bitrate = atoi(argv[3])) <= 0)
    {
        fprintf(stderr, "usage: %s <pcm16-48k.wav> <output.opus> <bitrate-kbps>\n", argv[0]);
        return 2;
    }
    input = fopen(argv[1], "rb");
    if (!input || !(output = fopen(argv[2], "wb")))
    {
        fprintf(stderr, "cannot open audio file: %s\n", strerror(errno));
        goto done;
    }
    if (fread(header, 1, sizeof(header), input) != sizeof(header) ||
        memcmp(header, "RIFF", 4) || memcmp(header + 8, "WAVE", 4))
    {
        fprintf(stderr, "not a RIFF/WAVE file\n");
        goto done;
    }
    while (fread(chunk, 1, sizeof(chunk), input) == sizeof(chunk))
    {
        const uint32_t chunk_size = le32(chunk + 4);
        if (!memcmp(chunk, "fmt ", 4))
        {
            unsigned char fmt[40];
            if (chunk_size < 16 || chunk_size > sizeof(fmt) ||
                fread(fmt, 1, chunk_size, input) != chunk_size)
                goto done;
            format = le16(fmt);
            channels = le16(fmt + 2);
            sample_rate = le32(fmt + 4);
            bits = le16(fmt + 14);
        }
        else if (!memcmp(chunk, "data", 4))
        {
            pcm_bytes = (unsigned char *)malloc(chunk_size);
            if (!pcm_bytes || fread(pcm_bytes, 1, chunk_size, input) != chunk_size)
                goto done;
            pcm_size = chunk_size;
            break;
        }
        else if (fseek(input, (long)(chunk_size + (chunk_size & 1)), SEEK_CUR) != 0)
            goto done;
    }
    if (format != 1 || sample_rate != 48000 || bits != 16 ||
        (channels != 1 && channels != 2) || !pcm_size || pcm_size % (channels * 2))
    {
        fprintf(stderr, "expected 16-bit PCM WAV at 48 kHz with one or two channels\n");
        goto done;
    }
    total_frames = pcm_size / (channels * 2);
    pcm = (int16_t *)pcm_bytes;
    encoder = opus_encoder_create(48000, channels, OPUS_APPLICATION_AUDIO, &opus_error);
    if (!encoder || opus_error != OPUS_OK ||
        opus_encoder_ctl(encoder, OPUS_SET_BITRATE(bitrate * 1000)) != OPUS_OK ||
        opus_encoder_ctl(encoder, OPUS_SET_VBR(1)) != OPUS_OK ||
        opus_encoder_ctl(encoder, OPUS_SET_COMPLEXITY(10)) != OPUS_OK ||
        opus_encoder_ctl(encoder, OPUS_GET_LOOKAHEAD(&pre_skip)) != OPUS_OK)
    {
        fprintf(stderr, "cannot configure Opus encoder\n");
        goto done;
    }
    if (ogg_stream_init(&stream, 0x46584f50) != 0)
        goto done;

    memset(opus_head, 0, sizeof(opus_head));
    memcpy(opus_head, "OpusHead", 8);
    opus_head[8] = 1;
    opus_head[9] = (unsigned char)channels;
    opus_head[10] = (unsigned char)(pre_skip & 0xff);
    opus_head[11] = (unsigned char)((pre_skip >> 8) & 0xff);
    opus_head[12] = 0x80; /* 48,000 Hz, little-endian */
    opus_head[13] = 0xbb;
    opus_head[14] = 0x00;
    opus_head[15] = 0x00;
    if (!packet_in(output, &stream, opus_head, sizeof(opus_head), 0, 0, 1))
        goto done_stream;
    memset(opus_tags, 0, sizeof(opus_tags));
    memcpy(opus_tags, "OpusTags", 8);
    opus_tags[8] = 4;
    memcpy(opus_tags + 12, "Flux", 4);
    if (!packet_in(output, &stream, opus_tags, sizeof(opus_tags), 0, 0, 1))
        goto done_stream;

    while (position < total_frames)
    {
        int16_t frame_pcm[960 * 2] = {0};
        uint32_t remaining = total_frames - position;
        uint32_t copied = remaining < (uint32_t)frame ? remaining : (uint32_t)frame;
        int bytes;
        memcpy(frame_pcm, pcm + position * channels, copied * channels * sizeof(int16_t));
        bytes = opus_encode(encoder, frame_pcm, frame, encoded, (opus_int32)sizeof(encoded));
        if (bytes < 0)
        {
            fprintf(stderr, "Opus encode error: %s\n", opus_strerror(bytes));
            goto done_stream;
        }
        position += copied;
        if (!packet_in(output, &stream, encoded, bytes, (ogg_int64_t)position + pre_skip,
                       position == total_frames, position == total_frames))
            goto done_stream;
    }
    success = 1;
done_stream:
    ogg_stream_clear(&stream);
done:
    if (encoder)
        opus_encoder_destroy(encoder);
    free(pcm_bytes);
    if (input)
        fclose(input);
    if (output)
        fclose(output);
    if (!success)
        remove(argv[2]);
    return success ? 0 : 1;
}
