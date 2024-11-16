\ENCODING=ISO-8859-1
\Problem name: 

Maximize
 objT9: x5
Subject To
 reach0:    M0 + s0 - s5  = 1
 reach1:    M1 + s1 - s6  = 0
 reach2:    M2 + s4 - s8  = 0
 reach3:    M3 + s2 - s7  = 0
 reach4:    M4 + s3 - s9  = 0
 reach5:    M5 - s1 - s2 + s5  = 0
 reach6:    M6 - s3 - s4 + s5  = 0
 reach7:    M7 - s0 + s6 + s7  = 0
 reach8:    M8 - s0 + s8 + s9  = 0
 flow9:     - x0 + x5  = 0
 flow10:    - x1 + x6  = 0
 flow11:    - x4 + x8  = 0
 flow12:    - x2 + x7  = 0
 flow13:    - x3 + x9  = 0
 flow14:    x1 + x2 - x5  = 0
 flow15:    x3 + x4 - x5  = 0
 flow16:    x0 - x6 - x7  = 0
 flow17:    x0 - x8 - x9  = 0
 little18:  M0 - 4 x0 >= 0
 little19:  M1 - x1 >= 0
 little20:  M3 - 6 x2 >= 0
 little21:  M4 - 8 x3 >= 0
 little22:  M2 - 3.5 x4 >= 0
 routing23: 0.3333 x6 - 0.6667 x7  = 0
 routing24: - 0.3333 x6 + 0.6667 x7  = 0
 routing25: 0.58824 x8 - 0.41176 x9  = 0
 routing26: - 0.58824 x8 + 0.41176 x9  = 0
End
