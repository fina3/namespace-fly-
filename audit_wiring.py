import json,sys,numpy as np
sys.path.insert(0,'/workspaces/doomfly')
import pyarrow.feather as feather
g=np.load('/workspaces/doomfly/outputs/doom/malecns_v1/graph.npz')
ptr,post,w,ids=g['ptr'],g['post'],g['weight'],g['ids']
n=len(ids);pre=np.repeat(np.arange(n),np.diff(ptr))
nodes=feather.read_table('/workspaces/doomfly/connectome_data/malecns_v1/normalized/neurons.feather').to_pandas()
ct=nodes.cell_type.fillna('?').astype(str).to_numpy();sc=nodes.superclass.fillna('?').astype(str).to_numpy()
cnt=np.load('/workspaces/results/s1/control/neuron_counts.npz')['counts']
def idx(t):return np.flatnonzero(ct==t)
p20,pe,wc=idx('DNp20'),idx('DNpe017'),idx('w-cHIN')
print('DNp20',ids[p20],'DNpe017',ids[pe],'w-cHIN n',len(wc))
def outs(src,name):
    m=np.isin(pre,src);t=post[m];ww=w[m]
    print(f'-- {name} outgoing rows {m.sum()} targets {len(np.unique(t))} sum|w| {abs(ww).sum():.1f} sign+ {(ww>0).sum()} sign- {(ww<0).sum()}')
    tu=np.unique(t);fired=tu[cnt[tu]>0]
    print('   targets that fire at all in control:',len(fired),'of',len(tu))
    import collections
    agg=collections.defaultdict(float)
    for a,b in zip(t,ww):agg[ct[a]]+=b
    top=sorted(agg.items(),key=lambda x:-abs(x[1]))[:8];print('   top target types (sum mV):',[(k,round(v,1)) for k,v in top])
outs(p20,'DNp20');outs(pe,'DNpe017')
# w-cHIN inputs
m=np.isin(post,wc);src=pre[m];ww=w[m]
import collections
agg=collections.defaultdict(float);act=collections.defaultdict(float)
for a,b in zip(src,ww):
    agg[ct[a]]+=b;act[ct[a]]+=b*cnt[a]
print('w-cHIN input rows',m.sum(),'from DNpe017 sum mV',ww[np.isin(src,pe)].sum(),'total + input mV',ww[ww>0].sum())
print('w-cHIN top inputs weighted by presyn control spikes:',[(k,round(v)) for k,v in sorted(act.items(),key=lambda x:-abs(x[1]))[:8]])
print('w-cHIN control spikes',cnt[wc].tolist())
# direct / 2-step DNpe017 -> DNp20
m=np.isin(pre,pe)&np.isin(post,p20);print('direct DNpe017->DNp20 rows',m.sum(),w[m].tolist())
m=np.isin(pre,wc)&np.isin(post,p20);print('w-cHIN->DNp20 rows',m.sum(),'sum',w[m].sum())
m=np.isin(post,p20);s=pre[m];print('DNp20 input rows',m.sum(),'active presyn',int((cnt[np.unique(s)]>0).sum()))
t1=np.unique(post[np.isin(pre,pe)]);m=np.isin(pre,t1)&np.isin(post,p20)
print('2-step DNpe017->X->DNp20: X types',sorted({ct[i] for i in pre[m]})[:20],'X active',sorted({ct[i] for i in pre[m] if cnt[i]>0}))
m=np.isin(pre,p20)&np.isin(post,pe);print('DNp20->DNpe017 rows',m.sum())
# common input DNp20_L & DNpe017_L
def ins(i):
    m=post==i;return dict(zip(pre[m],w[m]))
a,b=ins(int(np.flatnonzero(ids==10162)[0])),ins(int(np.flatnonzero(ids==10527)[0]))
sh=set(a)&set(b);drive=lambda d,keys:sum(d[k]*cnt[k] for k in keys)
print('DNp20_L inputs',len(a),'DNpe017_L inputs',len(b),'shared',len(sh),'frac of DNp20_L active drive from shared',round(drive(a,sh)/max(drive(a,a),1e-9),3),'DNpe017_L',round(drive(b,sh)/max(drive(b,b),1e-9),3))
print('top DNp20_L drivers',[(ct[k],int(ids[k]),round(a[k]*cnt[k])) for k in sorted(a,key=lambda k:-abs(a[k]*cnt[k]))[:5]])
print('top DNpe017_L drivers',[(ct[k],int(ids[k]),round(b[k]*cnt[k])) for k in sorted(b,key=lambda k:-abs(b[k]*cnt[k]))[:5]])
# sham candidates: descending neurons, active 15-45 Hz, not readouts, similar outgoing drive
deg=np.diff(ptr);ro={'DNa02','DNp09','MDN','MN9','DNp20','DNpe017'}
cand=[i for i in np.flatnonzero((sc=='descending_neuron')&(cnt>15*119)&(cnt<45*119)) if ct[i] not in ro]
print('sham candidates',len(cand))
rng=np.random.default_rng(20260927);pick=rng.choice(cand,size=min(6,len(cand)),replace=False)
for i in pick:print('SHAM',int(ids[i]),ct[i],'rate',round(cnt[i]/119,1),'outrows',int(deg[i]),'inrows',int((post==i).sum()))
print('ref DNpe017 outrows',deg[pe].tolist(),'DNp20 outrows',deg[p20].tolist())
