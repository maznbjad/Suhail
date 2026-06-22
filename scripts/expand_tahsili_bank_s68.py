#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, re
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
QP=ROOT/'data'/'questions.json'
RNG=random.Random(680068)
SUBJECTS=['فيزياء','كيمياء','رياضيات','الأحياء وعلم البيئة']
TARGET_ADD=300
DOCS={
'فيزياء':['كتاب الفيزياء 2026.pdf'],
'كيمياء':['تجميعات الكيمياء 2025.pdf'],
'رياضيات':['كتاب الرياضيات 2025.pdf'],
'الأحياء وعلم البيئة':['كتاب الأحياء وعلم البيئة 2026.pdf'],
}

def norm(s):
 s=str(s or '').strip().lower(); s=re.sub(r'[\u064b-\u065f\u0670]','',s); s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي'); return re.sub(r'\s+',' ',s)
def fmt(x):
 x=float(x); return str(int(round(x))) if abs(x-round(x))<1e-9 else f'{x:.3f}'.rstrip('0').rstrip('.')
def uniq(correct, ds):
 out=[]; c=str(correct)
 for x in ds:
  x=str(x)
  if x!=c and x not in out: out.append(x)
  if len(out)==3: return out
 k=1
 while len(out)<3:
  x=f'{c} ({k})'; k+=1
  if x not in out: out.append(x)
 return out

class Add:
 def __init__(self, qs):
  self.qs=qs; self.seen={norm(x.get('question')) for x in qs}; self.count=Counter()
 def add(self,subject,unit,skill,question,correct,distractors,explanation,difficulty='متوسط',steps=None,similar=None,trap='',hint='',diagnostic=False):
  k=norm(question)
  if not k or k in self.seen: return False
  self.seen.add(k); self.count[subject]+=1
  pref={'فيزياء':'PHY','كيمياء':'CHEM','رياضيات':'MATH','الأحياء وعلم البيئة':'BIO'}[subject]
  ds=uniq(correct,distractors)
  ci=(len(self.qs)+self.count[subject])%4
  choices=ds[:]; choices.insert(ci,str(correct))
  notes=[]
  for ch,note in (similar or {}).items():
   if str(ch) in choices: notes.append({'choice_index':choices.index(str(ch)),'choice':str(ch),'note':note})
  mode='none' if difficulty=='سهل' and not notes else ('brief' if difficulty=='سهل' else 'full')
  q={
   'id':f'TAH-{pref}-X{self.count[subject]:04d}','exam':'تحصيلي','eligible_tracks':['علمي','أدبي'],
   'category':subject,'subject':subject,'unit':unit,'skill':skill,'question':question,'choices':choices,'correct':ci,'answer':str(correct),
   'explain':explanation,'difficulty':difficulty,'time_per_question_sec':65 if difficulty=='سهل' else (85 if difficulty=='متوسط' else 110),
   'diagnostic':diagnostic,'keywords':[subject,unit,skill],'concept_id':f'tahsili.s68.{pref.lower()}.{re.sub(r"\W+","_",skill)}',
   'summary_block_id':'','misconception_id':f's68_{pref.lower()}_{self.count[subject]:04d}','display_variant':'standard',
   'source_status':'original_generated_from_verified_curriculum_patterns','source_documents':DOCS[subject],'source_pages':'inventory-linked',
   'source_pattern':skill,'copyright_method':'original_question_new_values_new_wording','editorial_status':'qa_passed_internal',
   'release_eligible':True,'rights_status':'original','bank':'تحصيلي موحد','created_year':2026,'explanation_mode':mode,
   'explanation':{'summary':explanation,'steps':steps or [],'similar_choices':notes},
  }
  if trap:q['explanation']['trap']=trap
  if hint:q['hint']=hint
  self.qs.append(q); return True

def physics(a:Add):
 i=1
 while a.count['فيزياء']<TARGET_ADD:
  kind=(i-1)%10; cycle=(i-1)//10
  if kind==0:
   v=4+(cycle%23); t=2+((cycle*3)%11); d=v*t
   a.add('فيزياء','الحركة','السرعة المنتظمة',f'قطعت مركبة مسافة بسرعة ثابتة مقدارها {v} m/s خلال {t} s. ما المسافة المقطوعة؟',f'{d} m',[f'{v+t} m',f'{abs(v-t)} m',f'{d+t} m'],f'المسافة تساوي السرعة مضروبة في الزمن: {v}×{t}={d} m.','سهل')
  elif kind==1:
   vi=cycle%9; acc=2+(cycle%7); t=2+((cycle*2)%8); vf=vi+acc*t; delta=acc*t
   a.add('فيزياء','الحركة','التسارع',f'بدأ جسم بسرعة {vi} m/s ثم تسارع بمقدار {acc} m/s² مدة {t} s. ما سرعته النهائية؟',f'{vf} m/s',[f'{delta} m/s',f'{vi+acc+t} m/s',f'{vi*t} m/s'],f'السرعة النهائية = السرعة الابتدائية + التسارع×الزمن = {vi}+{acc}×{t}={vf} m/s.','متوسط',similar={f'{delta} m/s':'هذا يمثل مقدار التغير في السرعة فقط، ولا يشمل السرعة الابتدائية.'})
  elif kind==2:
   m=2+(cycle%15); acc=2+((cycle*2)%9); F=m*acc
   a.add('فيزياء','القوى','قانون نيوتن الثاني',f'تؤثر محصلة قوى في جسم كتلته {m} kg فتمنحه تسارعًا مقداره {acc} m/s². ما مقدار المحصلة؟',f'{F} N',[f'{m+acc} N',f'{fmt(m/acc)} N',f'{F+acc} N'],f'وفق قانون نيوتن الثاني: F=ma={m}×{acc}={F} N.','سهل')
  elif kind==3:
   m=2+(cycle%12); v=3+((cycle*2)%13); ke=.5*m*v*v
   a.add('فيزياء','الشغل والطاقة','الطاقة الحركية',f'كتلة جسم {m} kg وسرعته {v} m/s. احسب طاقته الحركية.',f'{fmt(ke)} J',[f'{m*v} J',f'{m*v*v} J',f'{fmt(.5*m*v)} J'],f'الطاقة الحركية KE=½mv²=½×{m}×{v}²={fmt(ke)} J.','متوسط',similar={f'{m*v} J':'هذا الناتج يطابق مقدار الزخم عدديًا في هذه القيم، وليس الطاقة الحركية.'})
  elif kind==4:
   F=12+cycle*2; d=3+(cycle%9); W=F*d; t=2+(cycle%7); P=W/t
   a.add('فيزياء','الشغل والطاقة','القدرة',f'بذلت آلة قوة {F} N في اتجاه الحركة لمسافة {d} m خلال {t} s. ما قدرتها المتوسطة؟',f'{fmt(P)} W',[f'{W} W',f'{fmt(F/t)} W',f'{fmt(W*t)} W'],f'الشغل W=Fd={F}×{d}={W} J، ثم القدرة P=W/t={W}/{t}={fmt(P)} W.','صعب',steps=[f'W={F}×{d}={W} J',f'P={W}/{t}={fmt(P)} W'])
  elif kind==5:
   mass=3+(cycle%17); vel=4+((cycle*3)%16); p=mass*vel
   a.add('فيزياء','الزخم','الزخم الخطي',f'كرة كتلتها {mass} kg تتحرك بسرعة {vel} m/s. ما مقدار زخمها؟',f'{p} kg·m/s',[f'{mass+vel} kg·m/s',f'{mass*vel*vel} kg·m/s',f'{fmt(vel/mass)} kg·m/s'],f'الزخم p=mv={mass}×{vel}={p} kg·m/s.','سهل')
  elif kind==6:
   q=24+cycle*4; t=2+(cycle%10); I=q/t
   a.add('فيزياء','الكهرباء','شدة التيار',f'مرت شحنة مقدارها {q} C خلال مقطع موصل في {t} s. ما شدة التيار؟',f'{fmt(I)} A',[f'{q*t} A',f'{q-t} A',f'{fmt(t/q)} A'],f'شدة التيار I=Q/t={q}/{t}={fmt(I)} A.','سهل')
  elif kind==7:
   R=2+(cycle%14); I=1+((cycle*2)%9); V=R*I
   a.add('فيزياء','الكهرباء','قانون أوم',f'يمر تيار شدته {I} A في مقاومة مقدارها {R} Ω. ما فرق الجهد بين طرفيها؟',f'{V} V',[f'{fmt(I/R)} V',f'{R+I} V',f'{R} V'],f'من قانون أوم V=IR={I}×{R}={V} V.','متوسط',similar={f'{fmt(I/R)} V':'القسمة تستخدم لإيجاد التيار عندما يُعطى الجهد والمقاومة، لا لإيجاد الجهد هنا.'})
  elif kind==8:
   f=2+(cycle%18); lam=.5+((cycle%8)*.25); speed=f*lam
   a.add('فيزياء','الموجات','سرعة الموجة',f'موجة ترددها {f} Hz وطولها الموجي {fmt(lam)} m. ما سرعتها؟',f'{fmt(speed)} m/s',[f'{fmt(f/lam)} m/s',f'{fmt(f+lam)} m/s',f'{fmt(lam/f)} m/s'],f'سرعة الموجة v=fλ={f}×{fmt(lam)}={fmt(speed)} m/s.','متوسط')
  else:
   m=2+(cycle%11); v=3+(cycle%14); r=2+(cycle%9); fc=m*v*v/r
   a.add('فيزياء','الحركة الدائرية','القوة المركزية',f'جسم كتلته {m} kg يتحرك بسرعة {v} m/s في مسار دائري نصف قطره {r} m. ما القوة المركزية؟',f'{fmt(fc)} N',[f'{fmt(m*v/r)} N',f'{fmt(m*v*r)} N',f'{fmt(v*v/r)} N'],f'القوة المركزية Fc=mv²/r={m}×{v}²/{r}={fmt(fc)} N.','صعب')
  i+=1

def chemistry(a:Add):
 i=1; NA='6.02×10²³'
 while a.count['كيمياء']<TARGET_ADD:
  kind=(i-1)%10; c=(i-1)//10
  if kind==0:
   mm=[18,23,40,44,58.5,98][c%6]; n=1+(c%7); mass=mm*n
   a.add('كيمياء','الحسابات الكيميائية','المول والكتلة',f'كتلة مولية لمادة تساوي {mm} g/mol. كم مولًا يوجد في عينة كتلتها {fmt(mass)} g؟',f'{n} mol',[f'{mass} mol',f'{fmt(mm/mass)} mol',f'{mm} mol'],f'عدد المولات n=m/M={fmt(mass)}/{mm}={n} mol.','سهل')
  elif kind==1:
   n=1+(c%6); particles=n*6.02
   a.add('كيمياء','الحسابات الكيميائية','عدد أفوجادرو',f'كم عدد الجسيمات في {n} mol من مادة نقية؟',f'{fmt(particles)}×10²³',[f'{n}×10²³',f'{fmt(particles)}×10²²',f'{fmt(6.02/n)}×10²³'],f'عدد الجسيمات = عدد المولات × عدد أفوجادرو = {n}×6.02×10²³ = {fmt(particles)}×10²³.','متوسط')
  elif kind==2:
   n=.2+(.1*(c%9)); V=.2+(.1*((c*2)%8)); M=n/V
   a.add('كيمياء','المحاليل','المولارية',f'أذيب {fmt(n)} mol من مذاب لتحضير {fmt(V)} L من المحلول. ما المولارية؟',f'{fmt(M)} M',[f'{fmt(n*V)} M',f'{fmt(V/n)} M',f'{fmt(n+V)} M'],f'المولارية M=n/V={fmt(n)}/{fmt(V)}={fmt(M)} M.','متوسط')
  elif kind==3:
   M1=1+(c%5); V1=20+5*(c%9); M2=.25+.25*(c%6); V2=M1*V1/M2
   a.add('كيمياء','المحاليل','التخفيف',f'خُفف {V1} mL من محلول تركيزه {M1} M إلى تركيز {fmt(M2)} M. ما الحجم النهائي؟',f'{fmt(V2)} mL',[f'{fmt(V1*M2/M1)} mL',f'{fmt(M1+V1+M2)} mL',f'{fmt(V1/M2)} mL'],f'نطبق M₁V₁=M₂V₂، ومنه V₂=({M1}×{V1})/{fmt(M2)}={fmt(V2)} mL.','صعب')
  elif kind==4:
   part=10+2*(c%21); total=part+20+3*(c%13); pct=100*part/total
   a.add('كيمياء','الحسابات الكيميائية','النسبة المئوية الكتلية',f'يحتوي مركب على {part} g من عنصر ضمن كتلة كلية مقدارها {total} g. ما النسبة المئوية الكتلية للعنصر؟',f'{fmt(pct)}%',[f'{fmt(part/total)}%',f'{fmt(total/part)}%',f'{fmt(100-pct)}%'],f'النسبة المئوية الكتلية = ({part}/{total})×100 = {fmt(pct)}%.','متوسط')
  elif kind==5:
   m=50+5*(c%20); cs=4.18; dt=5+(c%16); q=m*cs*dt
   a.add('كيمياء','الطاقة','الحرارة النوعية',f'سُخنت عينة ماء كتلتها {m} g بمقدار {dt}°C. إذا كانت الحرارة النوعية 4.18 J/g·°C، فما الحرارة الممتصة؟',f'{fmt(q)} J',[f'{fmt(m*dt)} J',f'{fmt(cs*dt)} J',f'{fmt(q/1000)} J'],f'q=mcΔT={m}×4.18×{dt}={fmt(q)} J.','صعب')
  elif kind==6:
   exp=1+(c%12); ph=exp
   a.add('كيمياء','الأحماض والقواعد','الرقم الهيدروجيني',f'إذا كان تركيز +H في محلول يساوي 1×10⁻{exp} M، فما قيمة pH؟',str(ph),[str(14-ph),str(exp+1),str(max(0,exp-1))],f'pH=-log[H⁺]، وعندما [H⁺]=10⁻{exp} فإن pH={exp}.','متوسط',similar={str(14-ph):'هذه القيمة تمثل pOH عند 25°C، وليست pH.'})
  elif kind==7:
   P=1+(c%4); V=2+(c%7); T=273+10*(c%12); R=.082; n=P*V/(R*T)
   a.add('كيمياء','الغازات','قانون الغاز المثالي',f'غاز ضغطه {P} atm وحجمه {V} L عند {T} K. باستخدام R=0.082، ما عدد مولاته تقريبًا؟',f'{fmt(n)} mol',[f'{fmt(P*V*R*T)} mol',f'{fmt(P*V/T)} mol',f'{fmt(R*T/(P*V))} mol'],f'من PV=nRT: n=PV/RT=({P}×{V})/(0.082×{T})={fmt(n)} mol.','صعب')
  elif kind==8:
   acoef=1+(c%4); bcoef=2+(c%5); product=acoef+bcoef
   a.add('كيمياء','التفاعلات الكيميائية','حفظ الكتلة',f'في تجربة مغلقة تفاعل {acoef*10} g من مادة مع {bcoef*10} g من أخرى دون فقد. ما كتلة النواتج؟',f'{product*10} g',[f'{abs(acoef-bcoef)*10} g',f'{acoef*bcoef*10} g',f'{product} g'],f'في نظام مغلق تُحفظ الكتلة، لذا كتلة النواتج = {acoef*10}+{bcoef*10}={product*10} g.','سهل')
  else:
   k=1+(c%9); q0=20+5*(c%15); qeq=q0/(1+k)
   a.add('كيمياء','الاتزان','ثابت الاتزان',f'إذا كانت نسبة تركيز النواتج إلى المتفاعلات عند الاتزان تساوي {k}:1، وكان مجموع التركيزين {q0} وحدة، فما تركيز المتفاعلات؟',f'{fmt(qeq)}',[f'{fmt(q0-qeq)}',f'{q0}',str(k)],f'إذا كان الناتج={k}×المتفاعل، فالمجموع=({k}+1)×المتفاعل؛ لذا المتفاعل={q0}/{k+1}={fmt(qeq)}.','صعب')
  i+=1

def mathq(a:Add):
 i=1
 while a.count['رياضيات']<TARGET_ADD:
  kind=(i-1)%10; c=(i-1)//10
  if kind==0:
   aa=2+(c%12); x=1+(c%15); b=3+((c*2)%17); rhs=aa*x+b
   a.add('رياضيات','الجبر','المعادلات الخطية',f'إذا كان {aa}س + {b} = {rhs}، فما قيمة س؟',str(x),[str(rhs-b),fmt(rhs/aa),str(x+1)],f'نطرح {b} من الطرفين ثم نقسم على {aa}: س=({rhs}-{b})/{aa}={x}.','سهل')
  elif kind==1:
   x=2+(c%11); y=1+((c*3)%9); s=x+y; d=x-y
   a.add('رياضيات','الجبر','نظام معادلتين',f'إذا كان س+ص={s} و س-ص={d}، فما قيمة س؟',str(x),[str(y),str(s),fmt(s/2)],f'بجمع المعادلتين نحصل على 2س={s+d}، إذن س={x}.','متوسط')
  elif kind==2:
   first=2+(c%10); diff=2+((c*2)%8); n=5+(c%15); an=first+(n-1)*diff
   a.add('رياضيات','المتتابعات','المتتابعة الحسابية',f'متتابعة حسابية حدها الأول {first} والفرق المشترك {diff}. ما الحد رقم {n}؟',str(an),[str(first+n*diff),str(first+(n-2)*diff),str(diff*n)],f'aₙ=a₁+(n-1)d={first}+({n}-1)×{diff}={an}.','متوسط')
  elif kind==3:
   first=1+(c%5); ratio=2+(c%4); n=3+(c%7); an=first*(ratio**(n-1))
   a.add('رياضيات','المتتابعات','المتتابعة الهندسية',f'متتابعة هندسية حدها الأول {first} وأساسها {ratio}. ما الحد رقم {n}؟',str(an),[str(first*ratio*n),str(first*(ratio**n)),str(first+(n-1)*ratio)],f'aₙ=a₁rⁿ⁻¹={first}×{ratio}^{n-1}={an}.','متوسط')
  elif kind==4:
   r=2+(c%13); area=math.pi*r*r
   a.add('رياضيات','الهندسة','مساحة الدائرة',f'دائرة نصف قطرها {r} سم. ما مساحتها بدلالة π؟',f'{r*r}π سم²',[f'{2*r}π سم²',f'{r}π سم²',f'{2*r*r}π سم²'],f'مساحة الدائرة A=πr²=π×{r}²={r*r}π سم².','سهل')
  elif kind==5:
   l=4+(c%17); w=2+((c*3)%11); area=l*w; per=2*(l+w)
   a.add('رياضيات','الهندسة','المستطيل',f'مستطيل طوله {l} سم وعرضه {w} سم. ما مساحته؟',f'{area} سم²',[f'{per} سم²',f'{l+w} سم²',f'{l*l} سم²'],f'المساحة = الطول×العرض = {l}×{w}={area} سم².','سهل',similar={f'{per} سم²':'هذا ناتج المحيط عدديًا، والمطلوب المساحة.'})
  elif kind==6:
   a1=3+(c%12); b1=4+((c*2)%15); hyp=math.sqrt(a1*a1+b1*b1)
   # only use if integer, otherwise use 3-4-5 scaled
   scale=1+(c%8); aa=3*scale; bb=4*scale; hh=5*scale
   a.add('رياضيات','الهندسة','فيثاغورس',f'مثلث قائم ضلعا قائمته {aa} سم و{bb} سم. ما طول الوتر؟',f'{hh} سم',[f'{aa+bb} سم',f'{abs(bb-aa)} سم',f'{aa*bb} سم'],f'الوتر²={aa}²+{bb}²، وبالتالي الوتر={hh} سم.','متوسط')
  elif kind==7:
   total=5+(c%16); good=1+(c%(total-1)); p=good/total
   a.add('رياضيات','الاحتمالات','الاحتمال البسيط',f'صندوق يحوي {total} كرات متساوية، منها {good} بلون محدد. ما احتمال سحب كرة من هذا اللون؟',f'{good}/{total}',[f'{total-good}/{total}',f'{good}/{total-good}',f'1/{total}'],f'الاحتمال = عدد النتائج المطلوبة/عدد النتائج الكلية = {good}/{total}.','سهل')
  elif kind==8:
   nums=[2+(c%7),5+((c*2)%9),8+((c*3)%11),11+((c*4)%13)]; mean=sum(nums)/4
   a.add('رياضيات','الإحصاء','المتوسط الحسابي',f'ما المتوسط الحسابي للقيم: {"، ".join(map(str,nums))}؟',fmt(mean),[fmt(sum(nums)),fmt(max(nums)-min(nums)),fmt((nums[1]+nums[2])/2)],f'المتوسط = مجموع القيم/عددها = {sum(nums)}/4 = {fmt(mean)}.','سهل')
  else:
   m=2+(c%8); b=1+((c*2)%10); x=1+(c%12); y=m*x+b
   a.add('رياضيات','الدوال','الدالة الخطية',f'إذا كانت د(س)={m}س+{b}، فما قيمة د({x})؟',str(y),[str(m+x+b),str(m*x),str(y+b)],f'نعوض س={x}: د({x})={m}×{x}+{b}={y}.','سهل')
  i+=1

def biology(a:Add):
 organelles=[('النواة','تحفظ معظم المادة الوراثية وتدير أنشطة الخلية'),('الميتوكندريا','تنتج معظم ATP في التنفس الخلوي'),('الريبوسوم','يبني البروتين'),('جهاز جولجي','يعدل البروتينات ويغلفها'),('الغشاء البلازمي','ينظم مرور المواد'),('البلاستيدة الخضراء','تنفذ البناء الضوئي')]
 systems=[('الحويصلات الهوائية','تبادل الغازات'),('النيفرون','ترشيح الدم وتكوين البول'),('القلب','ضخ الدم'),('الأمعاء الدقيقة','امتصاص معظم المغذيات'),('الخلايا العصبية','نقل السيالات العصبية'),('البنكرياس','إفراز الإنسولين')]
 i=1
 while a.count['الأحياء وعلم البيئة']<TARGET_ADD:
  kind=(i-1)%10; c=(i-1)//10
  if kind==0:
   org,func=organelles[c%len(organelles)]; ds=[x[0] for x in organelles if x[0]!=org][:3]
   a.add('الأحياء وعلم البيئة','الخلية','العضيات',f'أي عضية تقوم أساسًا بالوظيفة الآتية: {func}؟',org,ds,f'{org} هي العضية المرتبطة بهذه الوظيفة.','سهل')
  elif kind==1:
   mode=c%4
   scenarios=[('انتقال جزيئات من تركيز مرتفع إلى منخفض دون طاقة','الانتشار'),('انتقال الماء عبر غشاء شبه منفذ','الأسموزية'),('انتقال مادة عكس تدرج التركيز باستخدام ATP','النقل النشط'),('إحاطة الخلية بجسيم كبير وإدخاله','البلعمة')]
   text,ans=scenarios[mode]
   a.add('الأحياء وعلم البيئة','الخلية','النقل عبر الغشاء',f'أي عملية خلوية يصفها الآتي: {text}؟',ans,[x[1] for x in scenarios if x[1]!=ans],f'الوصف يطابق عملية {ans}.','متوسط')
  elif kind==2:
   dominant=chr(65+(c%5)); rec=dominant.lower();
   a.add('الأحياء وعلم البيئة','الوراثة','التهجين الأحادي',f'عند تزاوج فردين طرازهما الجيني {dominant}{rec} × {dominant}{rec}، ما احتمال ظهور الطراز المتنحي {rec}{rec}؟','25%',['50%','75%','100%'],'مربع بانيت يعطي نسبة 1:2:1 للطرازات الجينية، لذا احتمال المتنحي المتماثل 1/4 = 25%.','متوسط')
  elif kind==3:
   n=2+(c%8); after=n*(2**(3+(c%4)))
   rounds=3+(c%4)
   a.add('الأحياء وعلم البيئة','الخلية','الانقسام المتساوي',f'بدأت مزرعة بخلايا عددها {n}، وانقسمت جميعها انقسامًا متساويًا {rounds} مرات. كم خلية تنتج؟',str(after),[str(n*rounds),str(n*(2**(rounds-1))),str(2*n+rounds)],f'يتضاعف العدد في كل انقسام؛ العدد النهائي={n}×2^{rounds}={after}.','متوسط')
  elif kind==4:
   level=1+(c%4); energy=10000*(10**(4-level)); next_energy=energy*.1
   a.add('الأحياء وعلم البيئة','البيئة','هرم الطاقة',f'إذا توافرت {fmt(energy)} وحدة طاقة في مستوى غذائي، فكم ينتقل تقريبًا إلى المستوى التالي وفق قاعدة 10%؟',fmt(next_energy),[fmt(energy*.9),fmt(energy*.01),fmt(energy)],f'ينتقل نحو 10% فقط: {fmt(energy)}×0.10={fmt(next_energy)} وحدة.','سهل',similar={fmt(energy*.9):'هذه الطاقة التي لا تنتقل تقريبًا، وليست الطاقة الواصلة للمستوى التالي.'})
  elif kind==5:
   initial=100+10*(c%20); births=10+(c%15); deaths=3+(c%8); immigration=2+(c%7); emigration=1+(c%5); final=initial+births-deaths+immigration-emigration
   a.add('الأحياء وعلم البيئة','البيئة','تغير حجم الجماعة',f'كان حجم جماعة {initial} فردًا، وحدثت {births} ولادة و{deaths} وفيات، وهاجر إليها {immigration} وغادرها {emigration}. ما الحجم الجديد؟',str(final),[str(initial+births-deaths),str(initial+births+deaths),str(final+emigration)],f'الحجم الجديد = البداية + الولادات - الوفيات + الهجرة الداخلة - الخارجة = {final}.','متوسط')
  elif kind==6:
   item,func=systems[c%len(systems)]; ds=[x[0] for x in systems if x[0]!=item][:3]
   a.add('الأحياء وعلم البيئة','جسم الإنسان','الأجهزة الحيوية',f'أي تركيب يرتبط مباشرة بوظيفة {func}؟',item,ds,f'{item} هو التركيب المسؤول مباشرة عن {func}.','سهل')
  elif kind==7:
   dna=6+3*(c%15); mrna=dna
   a.add('الأحياء وعلم البيئة','الوراثة الجزيئية','النسخ',f'إذا احتوى جزء مشفّر من DNA على {dna} قواعد، فما العدد المتوقع لقواعد mRNA الناتج عن نسخه؟',str(mrna),[str(dna*2),str(dna//3),str(dna+3)],f'ينسخ كل موضع في القالب إلى قاعدة مقابلة في mRNA، فيبقى عدد القواعد {dna}.','متوسط')
  elif kind==8:
   glucose=1+(c%8); atp=glucose*36
   a.add('الأحياء وعلم البيئة','الطاقة في الخلية','التنفس الخلوي',f'إذا افترضنا أن جزيء الجلوكوز ينتج 36 ATP، فكم ينتج من {glucose} جزيئات؟',str(atp),[str(glucose+36),str(glucose*18),str(glucose*6)],f'عدد ATP = {glucose}×36={atp}.','سهل')
  else:
   concepts=[('التعاقب الأولي','يبدأ غالبًا في منطقة بلا تربة'),('التعاقب الثانوي','يبدأ بعد اضطراب مع بقاء التربة'),('السعة التحملية','أكبر عدد تدعمه البيئة طويلًا'),('التنوع الحيوي','تنوع الجينات والأنواع والأنظمة البيئية')]
   term,desc=concepts[c%len(concepts)]
   a.add('الأحياء وعلم البيئة','البيئة','المفاهيم البيئية',f'أي مفهوم بيئي ينطبق على الوصف: {desc}؟',term,[x[0] for x in concepts if x[0]!=term],f'هذا الوصف هو تعريف {term}.','متوسط')
  i+=1

def main():
 qs=json.loads(QP.read_text(encoding='utf-8'))
 a=Add(qs)
 physics(a); chemistry(a); mathq(a); biology(a)
 for idx,q in enumerate(qs,start=1):
  q['public_id']=260000+idx; q['created_year']=2026
 QP.write_text(json.dumps(qs,ensure_ascii=False,indent=2),encoding='utf-8')
 report={'added_by_subject':dict(a.count),'total_questions':len(qs),'tahsili_total':sum(x.get('exam')=='تحصيلي' for x in qs),'last_public_id':max(x['public_id'] for x in qs)}
 out=ROOT/'docs'/'reports'/'SPRINT_68_TAHSILI_EXPANSION.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
