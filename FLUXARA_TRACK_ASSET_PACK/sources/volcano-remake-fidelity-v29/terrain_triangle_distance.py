import math
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def segment_intersects_triangle(a,b,t):
    edge1=sub(t[1],t[0]); edge2=sub(t[2],t[0]); direction=sub(b,a)
    p=cross(direction,edge2); determinant=dot(edge1,p)
    if abs(determinant)<1e-12:return False
    v=sub(a,t[0]); u=dot(v,p)/determinant
    if not -1e-10<=u<=1+1e-10:return False
    q=cross(v,edge1); w=dot(direction,q)/determinant
    if w < -1e-10 or u+w>1+1e-10:return False
    along=dot(edge2,q)/determinant
    return -1e-10<=along<=1+1e-10
def segment_distance(p0,p1,q0,q1):
    d1=sub(p1,p0); d2=sub(q1,q0); delta=sub(p0,q0)
    a,e=dot(d1,d1),dot(d2,d2); f=dot(d2,delta)
    if a<1e-20 and e<1e-20:return math.dist(p0,q0)
    if a<1e-20:s=0.; t=max(0,min(1,f/e))
    else:
        c=dot(d1,delta)
        if e<1e-20:t=0.;s=max(0,min(1,-c/a))
        else:
            b=dot(d1,d2); denominator=a*e-b*b
            s=max(0,min(1,(b*f-c*e)/denominator))if denominator>1e-20 else 0.
            t=(b*s+f)/e
            if t<0:t=0.;s=max(0,min(1,-c/a))
            elif t>1:t=1.;s=max(0,min(1,(b-c)/a))
    return math.dist([p0[k]+d1[k]*s for k in range(3)],[q0[k]+d2[k]*t for k in range(3)])
def triangle_distance(a,b):
    ae=[(a[i],a[(i+1)%3])for i in range(3)]; be=[(b[i],b[(i+1)%3])for i in range(3)]
    if any(segment_intersects_triangle(x,y,b)for x,y in ae)or any(segment_intersects_triangle(x,y,a)for x,y in be):return 0.
    return min([point_triangle_distance(p,b)for p in a]+[point_triangle_distance(p,a)for p in b]+[segment_distance(x,y,z,w)for x,y in ae for z,w in be])
def check_triangle_distance_geometry():
    base=[(-2.,0.,-2.),(2.,0.,-2.),(0.,0.,2.)]
    raised=[(x,y+5,z)for x,y,z in base]
    crossing=[(-1.,-2.,0.),(1.,2.,0.),(0.,1.,3.)]
    assert abs(triangle_distance(base,raised)-5)<1e-10
    assert triangle_distance(base,crossing)==0
    assert abs(segment_distance((0,0,0),(1,0,0),(0,2,0),(1,2,0))-2)<1e-10
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def point_triangle_distance(q,t):
 a,b,c=t;ab=sub(b,a);ac=sub(c,a);cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
 if dot(cross,cross)<1e-16:
  distances=[]
  for start,end in [(a,b),(b,c),(c,a)]:
   delta=sub(end,start);length=dot(delta,delta);u=max(0,min(1,dot(sub(q,start),delta)/length))if length else 0;distances.append(math.dist(q,[start[k]+u*delta[k]for k in range(3)]))
  return min(distances)
 ap=sub(q,a);d1,d2=dot(ab,ap),dot(ac,ap)
 if d1<=0 and d2<=0:return math.dist(q,a)
 bp=sub(q,b);d3,d4=dot(ab,bp),dot(ac,bp)
 if d3>=0 and d4<=d3:return math.dist(q,b)
 vc=d1*d4-d3*d2
 if vc<=0 and d1>=0 and d3<=0:
  v=d1/(d1-d3);return math.dist(q,[a[k]+v*ab[k]for k in range(3)])
 cp=sub(q,c);d5,d6=dot(ab,cp),dot(ac,cp)
 if d6>=0 and d5<=d6:return math.dist(q,c)
 vb=d5*d2-d1*d6
 if vb<=0 and d2>=0 and d6<=0:
  v=d2/(d2-d6);return math.dist(q,[a[k]+v*ac[k]for k in range(3)])
 va=d3*d6-d5*d4
 if va<=0 and d4-d3>=0 and d5-d6>=0:
  v=(d4-d3)/((d4-d3)+(d5-d6));return math.dist(q,[b[k]+v*(c[k]-b[k])for k in range(3)])
 total=va+vb+vc
 if abs(total)<1e-12:return min(math.dist(q,p)for p in t)
 v,u=vb/total,vc/total;return math.dist(q,[a[k]+v*ab[k]+u*ac[k]for k in range(3)])
