# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 2017

@author: Giuseppe Armenise
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import range
from builtins import object
from past.utils import old_div
from .functionset import *
import sys

def ARMAX_id(y,u,na,nb,nc,theta,max_iterations):
    val=max(na,nb+theta,nc)
    N=y.size-val
    eps=np.zeros(y.size)
    phi=np.zeros(na+nb+nc)
    PHI=np.zeros((N,na+nb+nc))
    for i in range(N):
        phi[0:na]=-y[i+val-1::-1][0:na]
        phi[na:na+nb]=u[val+i-1::-1][theta:nb+theta]
        PHI[i,:]=phi
    Vn=np.inf
    Vn_old=np.inf
    THETA=np.zeros(na+nb+nc)
    ID_THETA=np.identity(THETA.size)
    lambdak=0.5
    iterations=0
    Reached_max=False
    while (Vn_old>Vn or iterations==0) and iterations<max_iterations:
        THETA_old=THETA
        Vn_old=Vn
        iterations=iterations+1
        for i in range(N):
            PHI[i,na+nb:na+nb+nc]=eps[val+i-1::-1][0:nc]
        THETA=np.dot(np.linalg.pinv(PHI),y[val::])
        Vn=old_div((np.linalg.norm(y[val::]-np.dot(PHI,THETA),2)**2),(2*N))
        THETA_new=THETA
        lambdak=0.5
        while Vn>Vn_old:
            THETA=np.dot(ID_THETA*lambdak,THETA_new) + np.dot(ID_THETA*(1-lambdak),THETA_old)
            Vn=old_div((np.linalg.norm(y[val::]-np.dot(PHI,THETA),2)**2),(2*N))
            if lambdak<np.finfo(np.float32).eps:
                THETA=THETA_old
                Vn=Vn_old
            lambdak=old_div(lambdak,2.)
        eps[val::]=y[val::]-np.dot(PHI,THETA)
    if iterations>=max_iterations:
        print("Warning! Reached maximum iterations")
        Reached_max=True
    NUMG=np.zeros(val)
    DENG=np.zeros(val+1)
    DENG[0]=1.
    DENH=np.zeros(val+1)
    DENH[0]=1.
    NUMH=np.zeros(val+1)
    NUMH[0]=1.
    NUMG[theta:nb+theta]=THETA[na:na+nb]
    NUMH[1:nc+1]=THETA[na+nb::]
    DENG[1:na+1]=THETA[0:na]
    DENH[1:na+1]=THETA[0:na]
    return NUMG,DENG,NUMH,DENH,Vn,Reached_max

def select_order_ARMAX(y,u,tsample=1.,na_ord=[0,5],nb_ord=[1,5],nc_ord=[0,5],delays=[0,5],method='AIC',max_iterations=100):
    na_Min=min(na_ord)
    na_MAX=max(na_ord)+1
    nb_Min=min(nb_ord)
    nb_MAX=max(nb_ord)+1
    theta_Min=min(delays)
    theta_Max=max(delays)+1
    nc_Min=min(nc_ord)
    nc_MAX=max(nc_ord)+1
    if (type(na_Min+na_MAX+nb_Min+nb_MAX+theta_Min+theta_Max+nc_Min+nc_MAX)==int and na_Min>=0 and nb_Min>0 and nc_Min>=0 and theta_Min>=0)==False:
        sys.exit("Error! na, nc, theta must be positive integers, nb must be strictly positive integer")
#        return 0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,np.inf
    elif y.size!=u.size:
        sys.exit("Error! y and u must have tha same length")
#        return 0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,np.inf
    else:
        ystd,y=rescale(y)
        Ustd,u=rescale(u)
        IC_old=np.inf
        for i in range(na_Min,na_MAX):
            for j in range(nb_Min,nb_MAX):
                for k in range(theta_Min,theta_Max):
                    for l in range(nc_Min,nc_MAX):
                        useless1,useless2,useless3,useless4,Vn,Reached_max=ARMAX_id(y,u,i,j,l,k,max_iterations)
                        if Reached_max==True:
                            print("at Na=",i," Nb=", j, " Nc=",l, " Delay:",k)
                            print("-------------------------------------")
                        IC=information_criterion(i+j+l,y.size-max(i,j+k,l),Vn*2,method)
                        if IC<IC_old:
                            na_min,nb_min,nc_min,theta_min=i,j,l,k
                            IC_old=IC
        print("suggested orders are: Na=",na_min, "; Nb=",nb_min, "; Nc=",nc_min, "Delay: ",theta_min)
        NUMG,DENG,NUMH,DENH,Vn,useless1=ARMAX_id(y,u,na_min,nb_min,nc_min,theta_min,max_iterations)
        NUMG[theta_min:nb_min+theta_min]=NUMG[theta_min:nb_min+theta_min]*ystd/Ustd
        g_identif=cnt.tf(NUMG,DENG,tsample)
        h_identif=cnt.tf(NUMH,DENH,tsample)
        return na_min,nb_min,nc_min,theta_min,g_identif,h_identif,NUMG,DENG,NUMH,DENH,Vn

#creating object ARMAX model
class ARMAX_model(object):
    def __init__(self,na,nb,nc,theta,ts,NUMERATOR,DENOMINATOR,NUMERATOR_H,DENOMINATOR_H,G,H,Vn):
        self.na=na
        self.nb=nb
        self.nc=nc
        self.theta=theta
        self.ts=ts
        self.NUMERATOR=NUMERATOR
        self.DENOMINATOR=DENOMINATOR
        self.NUMERATOR_H=NUMERATOR_H
        self.DENOMINATOR_H=DENOMINATOR_H
        self.G=G
        self.H=H
        self.Vn=Vn