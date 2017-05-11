def evaluation(actions_states):
    #evaluation contains 3 parts
    cdef int WEIGHTS[7]
    WEIGHTS[:] = [-5, -8, 13, -4, 10, -5, 6]
    cdef unsigned long P_RINGS[7]
    P_RINGS[:] = [0x4281001818008142,
               0x42000000004200,
               0x2400810000810024,
               0x24420000422400,
               0x1800008181000018,
               0x18004242001800,
               0x3C24243C0000]
    cdef unsigned long P_CORNER = 0x8100000000000081
    cdef unsigned long P_SUB_CORNER = 0x42C300000000C342
    cdef unsigned long FULL_MASK = 0xFFFFFFFFFFFFFFFF
    results=[]
    score = []
    evalu={}
    cdef unsigned long BIT[64]
    BIT[:] = [1 << n for n in range(64)]

    cdef long mine_stab=0
    cdef long opp_stab=0
    cdef unsigned long mine = 0
    cdef unsigned long opp = 0


    cdef unsigned long m0 = 0
    cdef unsigned long m1 = 0
    cdef unsigned long m2 = 0
    cdef unsigned long m3 = 0
    cdef unsigned long o0 = 0
    cdef unsigned long o1 = 0
    cdef unsigned long o2 = 0
    cdef unsigned long o3 = 0
    cdef double scoreunstable = 0
    cdef double mpiece = 0
    cdef double opiece = 0
    cdef double scorepiece = 0
    cdef long mmob = 0
    cdef long scoremob = 0


    for p,S in actions_states:
        evalu[(p,S)]=0

        #stability
        mine_stab=0
        opp_stab=0
        p1_placed, p2_placed, previous, player = S
        mine = p1_placed if player == 2 else p2_placed
        opp = p2_placed if player == 2 else p1_placed

        m0 = mine & BIT[0] != 0
        m1 = mine & BIT[7] != 0
        m2 = mine & BIT[56] != 0
        m3 = mine & BIT[63] != 0
        o0 = opp & BIT[0] != 0
        o1 = opp & BIT[7] != 0
        o2 = opp & BIT[56] != 0
        o3 = opp & BIT[63] != 0

        if m0 != 1 and o0 != 1:
            mine_stab += (mine & BIT[1] != 0) + (mine & BIT[8] != 0) + (mine & BIT[9] != 0)
            opp_stab  += (opp  & BIT[1] != 0) + (opp  & BIT[8] != 0) + (opp  & BIT[9] != 0)
        if m1 != 1 and o1 != 1:
            mine_stab += (mine & BIT[6] != 0) + (mine & BIT[14] != 0) + (mine & BIT[15] != 0)
            opp_stab  += (opp  & BIT[6] != 0) + (opp  & BIT[14] != 0) + (opp  & BIT[15] != 0)
        if m2 != 1 and o2 != 1:
            mine_stab += (mine & BIT[48] != 0) + (mine & BIT[49] != 0) + (mine & BIT[57] != 0)
            opp_stab  += (opp  & BIT[48] != 0) + (opp  & BIT[49] != 0) + (opp  & BIT[57] != 0)
        if m3 != 1 and o3 != 1:
            mine_stab += (mine & BIT[62] != 0) + (mine & BIT[54] != 0) + (mine & BIT[55] != 0)
            opp_stab  += (opp  & BIT[62] != 0) + (opp  & BIT[54] != 0) + (opp  & BIT[55] != 0)

        scoreunstable = - 30.0 * (mine_stab - opp_stab)

        # piece difference
        mpiece = (m0 + m1 + m2 + m3) * 100.0
        for i in range(len(WEIGHTS)):
            mpiece += WEIGHTS[i] * count_bit(mine & P_RINGS[i])
        opiece = (o0 + o1 + o2 + o3) * 100.0

        for i in range(len(WEIGHTS)):
            opiece += WEIGHTS[i] * count_bit(opp  & P_RINGS[i])

        scorepiece = mpiece - opiece

        # mobility@Why only white conpute the mob value
        mmob = count_bit(move_gen(mine, opp))
        scoremob = 20 * mmob

        evalu[(p,S)]=scorepiece + scoreunstable + scoremob

       #if(p[0]==2 or p[0]==5):
    #   evalu[(p,S)]+=1
       #if(p[1]==2 or p[1]==5):
     #   evalu[(p,S)]+=1
    #if(p[0]==0 or p[0]==7):
        #   evalu[(p,S)]+=2
        #if(p[1]==0 or p[1]==7):
        #   evalu[(p,S)]+=2

    T = sorted(evalu.items(),key=lambda item:item[1],reverse=True)

    for t in range(len(T)):
        results.append(T[t][0])
    #result = [(p,S) for i in T[i][0]]
    #print results
        score.append(T[t][1])
    #print T[1][1], T[2][1]
    cdef long t1 = T[1][1]
    cdef long t2 = T[2][1]
    if(t1==0):
        t1=1
    if(t2==0):
        t2=1

#    if(((T[0][1]-t1)/abs(t1))>0.25):
#        return results[0:1],score[0:1]
#    else:
#        if(((T[0][1]-t2)/abs(t2))>0.35):
#            return results[0:2],score[0:2]
#        else:
#            return results[0:3],score[0:3]
    return results, score

def count_bit(unsigned long b):
    cdef unsigned long FULL_MASK = 0xFFFFFFFFFFFFFFFF
    b -=  (b >> 1) & 0x5555555555555555
    b  = (((b >> 2) & 0x3333333333333333) + (b & 0x3333333333333333))
    b  = ((b >> 4) + b)  & 0x0F0F0F0F0F0F0F0F
    return ((b * 0x0101010101010101) & FULL_MASK) >> 56


def move_gen_sub(P, mask, dir):
    cdef unsigned long dir2 = long(dir * 2)
    cdef unsigned long flip1  = mask & (P << dir)
    cdef unsigned long flip2  = mask & (P >> dir)
    flip1 |= mask & (flip1 << dir)
    flip2 |= mask & (flip2 >> dir)
    cdef unsigned long mask1  = mask & (mask << dir)
    cdef unsigned long mask2  = mask & (mask >> dir)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    return (flip1 << dir) | (flip2 >> dir)

def move_gen(P, O):
    cdef unsigned long FULL_MASK = 0xFFFFFFFFFFFFFFFF
    cdef unsigned long mask = O & 0x7E7E7E7E7E7E7E7E
    return ((move_gen_sub(P, mask, 1)
            | move_gen_sub(P, O, 8)
            | move_gen_sub(P, mask, 7)
            | move_gen_sub(P, mask, 9)) & ~(P|O)) & FULL_MASK
