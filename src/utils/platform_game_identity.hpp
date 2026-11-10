#ifndef PLATFORM_GAME_IDENTITY_HPP
#define PLATFORM_GAME_IDENTITY_HPP
// Product/resource identity is independent of the shared engine's internal symbols.
#if defined(ANDROID) || defined(__ANDROID__)
# define PLATFORM_GAME_LITERAL(android_value, other_value) android_value
#else
# define PLATFORM_GAME_LITERAL(android_value, other_value) other_value
#endif
#endif
