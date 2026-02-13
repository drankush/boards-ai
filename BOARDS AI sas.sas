

dm 'odsresults; clear';

OPTIONS nofmterr;

/*import dataset*/
data work.et; set r.et; run;


data et; set et; 
if clarity = 5 then clarity5=1; else if clarity ne 5 then clarity5=0;
if clarity ge 4 then clarity4=1; else if clarity < 4 then clarity4=0;
if clinical_relevance = 5 then clinical_relevance5=1; else if clinical_relevance ne 5 then clinical_relevance5=0;
if clinical_relevance ge 4 then clinical_relevance4=1; else if clinical_relevance < 4 then clinical_relevance4=0;
if difficulty = 5 then difficulty5=1; else if difficulty ne 5 then difficulty5=0;
if difficulty ge 4 then difficulty4=1; else if difficulty < 4 then difficulty4=0;
if option_accuracy = 5 then option_accuracy5=1; else if option_accuracy ne 5 then option_accuracy5=0;
if option_accuracy ge 4 then option_accuracy4=1; else if option_accuracy < 4 then option_accuracy4=0;
if assessment_accuracy = 5 then assessment_accuracy5=1; else if assessment_accuracy ne 5 then assessment_accuracy5=0;
if assessment_accuracy ge 4 then assessment_accuracy4=1; else if assessment_accuracy < 4 then assessment_accuracy4=0;
if feedback_quality = 5 then feedback_quality5=1; else if feedback_quality ne 5 then feedback_quality5=0;
if feedback_quality ge 4 then feedback_quality4=1; else if feedback_quality < 4 then feedback_quality4=0;
run;

*unique question model identifier*;
data et; set et;
id_ques_model=CAT(case_id,'_',mcq_id,'_',model_id);
RUN;


*two composite metrics: 
question generation accuracy (combining clarity, clinical relevance, and option accuracy)
and overall assessment accuracy (combining assessment accuracy and feedback quality) 
*;
data et; set et; qga5=0; qga4=0; oaa5=0; oaa4=0; 
qga=mean(clarity,clinical_relevance,option_accuracy);
oaa=mean(assessment_accuracy,feedback_quality);

if clarity = 5 and clinical_relevance = 5 and option_accuracy = 5 then do; qga5=1;end;
if clarity ge 4 and clinical_relevance ge 4 and option_accuracy ge 4 then do; qga4=1;end;

if assessment_accuracy = 5 and feedback_quality = 5  then do; oaa5=1;end;
if assessment_accuracy ge 4 and feedback_quality ge 4  then do; oaa4=1;end;
run;


proc sort data=et; by id_ques_model; run;
proc sql; create table et2 as
    select *, sum(clarity5) as count_clarity5, sum(clarity4) as count_clarity4, mean(clarity) as avg_clarity,
	sum(clinical_relevance5) as count_clinical_relevance5, sum(clinical_relevance4) as count_clinical_relevance4, mean(clinical_relevance) as avg_clinical_relevance,
sum(difficulty5) as count_difficulty5, sum(difficulty4) as count_difficulty4, mean(difficulty) as avg_difficulty,
sum(option_accuracy5) as count_option_accuracy5, sum(option_accuracy4) as count_option_accuracy4, mean(option_accuracy) as avg_option_accuracy,
sum(assessment_accuracy5) as count_assessment_accuracy5, sum(assessment_accuracy4) as count_assessment_accuracy4, mean(assessment_accuracy) as avg_assessment_accuracy,
sum(feedback_quality5) as count_feedback_quality5, sum(feedback_quality4) as count_feedback_quality4, mean(feedback_quality) as avg_feedback_quality,
sum(qga5) as count_qga5, sum(qga4) as count_qga4, mean(qga) as avg_qga,
sum(oaa5) as count_oaa5, sum(oaa4) as count_oaa4, mean(oaa) as avg_oaa
    from et
    group by id_ques_model;
quit;


data et2; set et2;
if count_clarity5 in (2,3) then tba_clarity = 1; else if count_clarity5 in (0,1) then tba_clarity = 0;
if avg_clarity ge 4 then as4a_clarity=1; else if avg_clarity < 4 then as4a_clarity = 0;
if count_clarity4 in (3) then t2ba_clarity = 1; else if count_clarity4 in (0,1,2) then t2ba_clarity = 0;
if count_clarity5 in (3) then p5a_clarity = 1; else if count_clarity5 in (0,1,2) then p5a_clarity = 0;

if count_clinical_relevance5 in (2,3) then tba_clinical_relevance = 1; else if count_clinical_relevance5 in (0,1) then tba_clinical_relevance = 0;
if avg_clinical_relevance ge 4 then as4a_clinical_relevance=1; else if avg_clinical_relevance < 4 then as4a_clinical_relevance = 0;
if count_clinical_relevance4 in (3) then t2ba_clinical_relevance = 1; else if count_clinical_relevance4 in (0,1,2) then t2ba_clinical_relevance = 0;
if count_clinical_relevance5 in (3) then p5a_clinical_relevance = 1; else if count_clinical_relevance5 in (0,1,2) then p5a_clinical_relevance = 0;

if count_option_accuracy5 in (2,3) then tba_option_accuracy = 1; else if count_option_accuracy5 in (0,1) then tba_option_accuracy = 0;
if avg_option_accuracy ge 4 then as4a_option_accuracy=1; else if avg_option_accuracy < 4 then as4a_option_accuracy = 0;
if count_option_accuracy4 in (3) then t2ba_option_accuracy = 1; else if count_option_accuracy4 in (0,1,2) then t2ba_option_accuracy = 0;
if count_option_accuracy5 in (3) then p5a_option_accuracy = 1; else if count_option_accuracy5 in (0,1,2) then p5a_option_accuracy = 0;

if count_assessment_accuracy5 in (2,3) then tba_assessment_accuracy = 1; else if count_assessment_accuracy5 in (0,1) then tba_assessment_accuracy = 0;
if avg_assessment_accuracy ge 4 then as4a_assessment_accuracy=1; else if avg_assessment_accuracy < 4 then as4a_assessment_accuracy = 0;
if count_assessment_accuracy4 in (3) then t2ba_assessment_accuracy = 1; else if count_assessment_accuracy4 in (0,1,2) then t2ba_assessment_accuracy = 0;
if count_assessment_accuracy5 in (3) then p5a_assessment_accuracy = 1; else if count_assessment_accuracy5 in (0,1,2) then p5a_assessment_accuracy = 0;

if count_difficulty5 in (2,3) then tba_difficulty = 1; else if count_difficulty5 in (0,1) then tba_difficulty = 0;
if avg_difficulty ge 4 then as4a_difficulty=1; else if avg_difficulty < 4 then as4a_difficulty = 0;
if count_difficulty4 in (3) then t2ba_difficulty = 1; else if count_difficulty4 in (0,1,2) then t2ba_difficulty = 0;
if count_difficulty5 in (3) then p5a_difficulty = 1; else if count_difficulty5 in (0,1,2) then p5a_difficulty = 0;

if count_feedback_quality5 in (2,3) then tba_feedback_quality = 1; else if count_feedback_quality5 in (0,1) then tba_feedback_quality = 0;
if avg_feedback_quality ge 4 then as4a_feedback_quality=1; else if avg_feedback_quality < 4 then as4a_feedback_quality = 0;
if count_feedback_quality4 in (3) then t2ba_feedback_quality = 1; else if count_feedback_quality4 in (0,1,2) then t2ba_feedback_quality = 0;
if count_feedback_quality5 in (3) then p5a_feedback_quality = 1; else if count_feedback_quality5 in (0,1,2) then p5a_feedback_quality = 0;

if count_oaa5 in (2,3) then tba_oaa = 1; else if count_oaa5 in (0,1) then tba_oaa = 0;
if avg_oaa ge 4 then as4a_oaa=1; else if avg_oaa < 4 then as4a_oaa = 0;
if count_oaa4 in (3) then t2ba_oaa = 1; else if count_oaa4 in (0,1,2) then t2ba_oaa = 0;
if count_oaa5 in (3) then p5a_oaa = 1; else if count_oaa5 in (0,1,2) then p5a_oaa = 0;

if count_qga5 in (2,3) then tba_qga = 1; else if count_qga5 in (0,1) then tba_qga = 0;
if avg_qga ge 4 then as4a_qga=1; else if avg_qga < 4 then as4a_qga = 0;
if count_qga4 in (3) then t2ba_qga = 1; else if count_qga4 in (0,1,2) then t2ba_qga = 0;
if count_qga5 in (3) then p5a_qga = 1; else if count_qga5 in (0,1,2) then p5a_qga = 0;
run;


proc sort data=et2; by id_ques_model; run;
data et2_first; set et2; if first.id_ques_model; by id_ques_model ; run;
data et2_first; set et2_first; drop rater clarity clinical_relevance difficulty option_accuracy assessment_accuracy feedback_quality ; run;


%macro borda(var);
proc genmod data=et2;
class  model_id (ref='GM') id_ques_model ;
model &var=model_id / dist=normal link=identity;
    repeated subject=id_ques_model / ;	lsmeans model_id /  cl adjust=tukey;
run;
%mend;

%borda(clarity);
%borda(clinical_relevance);
%borda(option_accuracy);
%borda(assessment_accuracy);
%borda(feedback_quality);




/*models clustered by rater*/
%macro g(var);
proc freq data=et2_first; table model_id*&var/nocol nopercent ; run;
proc genmod data=et2 ;
class &var model_id id_ques_model;
model &var (event='1')=model_id / d=bin link=logit type3;
repeated subject=id_ques_model / type=cs;
lsmeans model_id /ilink pdiff cl adjust=tukey;
run;%mend;

%g(tba_clarity);
%g(as4a_clarity);
%g(t2ba_clarity);
%g(p5a_clarity);

%g(tba_clinical_relevance);
%g(as4a_clinical_relevance);
%g(t2ba_clinical_relevance);
%g(p5a_clinical_relevance);

%g(tba_option_accuracy);
%g(as4a_option_accuracy);
%g(t2ba_option_accuracy);
%g(p5a_option_accuracy);

%g(tba_qga);
%g(as4a_qga);
%g(t2ba_qga);
%g(p5a_qga);

%g(tba_assessment_accuracy);
%g(as4a_assessment_accuracy);
%g(t2ba_assessment_accuracy);
%g(p5a_assessment_accuracy);

%g(tba_feedback_quality);
%g(as4a_feedback_quality);
%g(t2ba_feedback_quality);
%g(p5a_feedback_quality);

%g(tba_oaa);
%g(as4a_oaa);
%g(t2ba_oaa);
%g(p5a_oaa);

%g(tba_difficulty);
%g(as4a_difficulty);
%g(t2ba_difficulty);
%g(p5a_difficulty);

*did not converge*;
proc freq data=et2_first; table model_id*as4a_qga/nocol nopercent FISHER CHISQ; run;
proc freq data=et2_first; table model_id*tba_assessment_accuracy/nocol nopercent FISHER CHISQ; run;
proc freq data=et2_first; table model_id*as4a_assessment_accuracy/nocol nopercent FISHER CHISQ; run;
proc freq data=et2_first; table model_id*as4a_feedback_quality/nocol nopercent FISHER CHISQ; run;
proc freq data=et2_first; table model_id*as4a_oaa/nocol nopercent FISHER CHISQ; run;



/*t2ba: all raters ge 4*/
%macro gP(var);
proc freq data=et2_first; table model_id*&var/nocol nopercent ; run;
proc genmod data=et2 ;
class &var model_id (ref='GM') id_ques_model;
model &var (event='1')=model_id / d=bin link=logit type3;
repeated subject=id_ques_model / type=cs;
lsmeans model_id /ilink pdiff cl  oddsratio adjust=tukey;
run;%mend;

%gP(t2ba_clarity);

%gP(t2ba_clinical_relevance);

%gP(t2ba_option_accuracy);

%gP(t2ba_qga);

%gP(t2ba_assessment_accuracy);

%gP(t2ba_feedback_quality);

%gP(t2ba_oaa);

%gP(t2ba_difficulty);




/*p5a: all raters =5*/
%macro gP(var);
proc freq data=et2_first; table model_id*&var/nocol nopercent ; run;
proc genmod data=et2 ;
class &var model_id (ref='GM') id_ques_model;
model &var (event='1')=model_id / d=bin link=logit type3;
repeated subject=id_ques_model / type=cs;
lsmeans model_id /ilink pdiff cl  oddsratio adjust=tukey;
run;%mend;


%gP(p5a_clarity);

%gP(p5a_clinical_relevance);

%gP(p5a_option_accuracy);

%gP(p5a_qga);

%gP(p5a_assessment_accuracy);

%gP(p5a_feedback_quality);

%gP(p5a_oaa);

%gP(p5a_difficulty);
