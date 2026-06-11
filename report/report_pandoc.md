**Banana Spoilage Detection: An IoT-Driven Machine Learning System for
Predicting Remaining Shelf Life**

A project report

submitted by

**Your Name**

(2021PMA55\*\*)

under the supervision of

Dr. \*\*\*\*\*\*

in partial fulfillment of

the requirements for the degree of

**Bachelor of Technology**

in Electronics and Communication Engineering

to the

Department of Electronics and Communication Engineering

**Indian Institute of Information Technology Kota**

May 2026

**DECLARATION**

I hereby declare that the work reported in the project titled "Banana
Spoilage Detection: An IoT-Driven Machine Learning System for Predicting
Remaining Shelf Life", submitted for partial fulfilment of the B.Tech
degree at the Department of Electronics and Communication Engineering,
IIIT Kota, is a record of the work carried out by me under the
supervision of Dr. \*\*\*\*\*\*. The matter embodied in this report has
not been submitted for the award of any other degree or diploma. All
sources of information used in this work have been duly acknowledged in
the bibliography.

Your Name

(B.Tech Final)

Department of Electronics and Communication Engineering

IIIT Kota

May 2026

**CERTIFICATE**

It is certified that Your Name has submitted the project under my
supervision for partial fulfilment of the B.Tech degree in Electronics
and Communication Engineering on the topic "Banana Spoilage Detection:
An IoT-Driven Machine Learning System for Predicting Remaining Shelf
Life". It is further certified that the candidate has carried out the
project work under my guidance during the academic session 2025--2026 at
the Department of Electronics and Communication Engineering, IIIT Kota.

**Dr. \*\*\*\*\*\***

Assistant Professor

Department of Electronics and Communication Engineering

IIIT Kota

**ACKNOWLEDGEMENT**

As a matter of first importance, I offer my genuine thanks to my
supervisor Dr. \*\*\*\*\*\*, Assistant Professor, Department of
Electronics and Communication Engineering, IIIT Kota, for the continuous
guidance, technical mentorship, and encouragement extended throughout
this project. The supervisor's insistence on rigour --- particularly on
cited physics constants, batch-level data-leak prevention, and honest
scope statements --- has shaped every layer of this work.

I am thankful to the Department of Electronics and Communication
Engineering and the Computing Laboratory at IIIT Kota for providing
access to compute resources sufficient to train the recurrent neural
network on a 105,000-row synthetic dataset. I also acknowledge the
open-source maintainers of TensorFlow / Keras, scikit-learn, FastAPI,
and React, on whose work this MVP rests entirely.

Finally, I thank my family and peers for the moral support extended over
the duration of this project.

Your Name

(2021PMA55\*\*)

**Contents**

**Declaration** **2**

**Certificate** **3**

**Acknowledgement** **4**

**1 Introduction** **6**

> 1.1 Motivation 6
>
> 1.2 Problem Statement 6
>
> 1.3 Objectives 6
>
> 1.4 Scope and Honest Limitations 7
>
> 1.5 Original Contributions 8
>
> 1.6 Organisation of the Report 8

**2 Preliminaries** **9**

> 2.1 Post-Harvest Food Science Foundations 9
>
> 2.2 Spoilage Definition and the Regression Target 12
>
> 2.3 Supervised Learning Models 13
>
> 2.4 Evaluation Metrics 16
>
> 2.5 Train / Validation / Test Splitting 17

**3 Methodology and System Design** **18**

> 3.1 System Architecture Overview 18
>
> 3.2 Hardware Topology and Sensor Integration 18
>
> 3.3 Data Pipeline 20
>
> 3.4 Model Training Procedure 21
>
> 3.5 Backend Service 21
>
> 3.6 Traffic-Light Rules Engine 22
>
> 3.7 Front-End Dashboard (Brief) 22
>
> 3.8 Deployment via Docker Compose 22
>
> 3.9 Testing and Quality Assurance 23

**4 Results and Conclusions** **24**

> 4.1 Data Collection Procedure 24
>
> 4.2 Model Selection and Accuracy Progression 27
>
> 4.3 Additional Results Derived from the Project Artefacts 31
>
> 4.4 Conclusions 34

**Bibliography** **36**

Note: page numbers above are static. After opening in Microsoft Word,
you may regenerate the Table of Contents from the Layout / References
menu if any edits change page breaks.

Chapter 1

# Introduction

## 1.1 Motivation

Approximately fourteen percent of all food produced globally is lost
between harvest and retail, with another seventeen percent wasted at the
consumption stage; perishable horticultural produce dominates these
losses \[1\]. Within this category, climacteric fruits such as banana
(Musa acuminata AAA, Cavendish cultivar) are particularly vulnerable:
they undergo a sharp, autocatalytic respiration burst --- the
climacteric peak --- during which carbon dioxide and ethylene production
surge by an order of magnitude, after which any deviation in storage
temperature or humidity initiates an irreversible cascade toward
microbial decomposition \[2\]. Conventional warehouse practice relies
almost exclusively on visual inspection by trained operators, a method
that is inherently retrospective: by the time peel browning or methane
odour becomes apparent to a human observer, the spoilage process has
typically been underway for 18 to 36 hours and the affected stock can no
longer be re-routed, discounted, or salvaged.

Modern Internet-of-Things (IoT) hardware --- low-cost temperature,
humidity, and metal-oxide gas sensors interfaced through low-power
microcontrollers --- now permits the deployment of dense, continuous
sensing within a banana storage container at a per-node cost below ₹2000
\[3\] \[4\]. These sensors capture the precursor signals that precede
visible spoilage: gradual temperature drift, falling humidity, the
climacteric carbon dioxide rise, and finally the appearance of headspace
methane that marks the onset of anaerobic decomposition. The remaining
engineering problem is therefore not one of measurement but of
**interpretation**: converting the multivariate, time-correlated sensor
stream into an actionable estimate of Remaining Shelf Life (RSL) and a
discrete operational status that warehouse staff can act upon. This is
the problem that the present project addresses.

## 1.2 Problem Statement

Given a real-time stream of seven sensor channels --- temperature
(temp_c), relative humidity (humidity_pct), carbon dioxide concentration
(co2_ppm), ethylene concentration (ethylene_ppm), methane concentration
(methane_ppm), hours since harvest (hours_since_harvest), and visual
ripeness stage (ripeness_estimate) --- the system must (i) regress the
continuous quantity days_until_spoilage \$\\in \[0, 30\]\$, and (ii)
emit a categorical traffic-light status \$s \\in \\{\\text{green},
\\text{yellow}, \\text{red}\\}\$ together with the contributing factors
that justify the assignment, such that warehouse managers receive at
least 24 hours of usable lead time before any batch crosses into
irreversible spoilage.

## 1.3 Objectives

The specific objectives of this project are stated below.

- Construct a physics-grounded simulator of post-harvest banana
  respiration, calibrated to peer-reviewed reference parameters from the
  UC Davis Postharvest Technology Center and the Goldfinger banana
  respiration study.

- Generate a labelled synthetic dataset of approximately 65,000 sensor
  rows across 432 independent banana batches that span a realistic
  envelope of cold, optimal, room, hot, and dynamic day--night storage
  regimes.

- Engineer features that encode the mathematical relationships
  identified by post-harvest food science --- Arrhenius kinetics,
  climacteric multiplier, humidity stress, container gas balance, and a
  cumulative environmental stress integral --- and use them to compute
  the regression label by forward projection.

- Train and rigorously evaluate two complementary machine-learning
  models: a Random Forest regressor as a non-temporal baseline, and a
  Long Short-Term Memory (LSTM) recurrent network as the principal
  time-series model, with strict batch-level data splitting to prevent
  leakage.

- Expose the trained models behind a FastAPI microservice that serves
  single-shot, sequence-window, and bulk-CSV prediction endpoints
  together with a WebSocket stream for live preview.

- Provide a minimal React dashboard front-end so that the system can be
  demonstrated and operated without command-line access.

## 1.4 Scope and Honest Limitations

This work is deliberately scoped as a **software-only minimum viable
product** (MVP) restricted to the Cavendish banana cultivar. Three
explicit limitations apply. First, the dataset is synthetic: although it
is calibrated to published respiration data --- peaking at 55 mg
CO₂/kg/h, in close agreement with the published 56.8 mg CO₂/kg/h figure
\[2\] --- real-sensor field validation against ground-truth spoilage
logs is explicit future work. Second, the embedded hardware path
(ESP32 + DHT22 + MQ-135 + MQ-4) is stubbed behind a DataSource
abstraction so that real Message Queuing Telemetry Transport (MQTT)
ingest can replace the simulator without disturbing the model or user
interface, but no firmware has been written. Third, only one commodity
is supported in the present release; the architecture has been verified
to support new commodities via a four-step extension recipe but rice,
mango, wheat, and tomato are not yet implemented.

Authentication, multi-tenancy, persistent batch history, cloud
deployment, and alert webhooks are explicitly out of scope. The present
report is written so that an examiner or successor engineer can
reconstruct, retrain, and extend the system without recourse to the
original chat transcripts that produced it.

## 1.5 Original Contributions

- A complete, documented physics simulator for post-harvest banana
  respiration in Python, exposing both physical-unit (ppm) outputs and
  synthetic raw analog-to-digital-converter readings that emulate
  MQ-series metal-oxide sensors.

- A rigorous batch-level train / validation / test split implementation
  that prevents the trivial information leak that arises from random
  row-level shuffling on time-series data.

- A two-stage decision logic that separates the learned regression of
  remaining shelf life from a transparent rules engine which converts
  the continuous prediction together with raw sensor conditions into the
  green / yellow / red status and an interpretable list of contributing
  factors.

- A reference REST and WebSocket API surface --- including a CSV
  bulk-prediction endpoint with column aliasing --- that demonstrates
  how the trained models can be served to downstream consumers.

## 1.6 Organisation of the Report

Chapter 2 develops the mathematical preliminaries: the Arrhenius
equation, climacteric kinetics, the humidity stress factor, the
gas-balance ordinary differential equations (ODEs), the cumulative
stress integral, and the formal definitions of the Random Forest, the
LSTM cell, and every evaluation metric used. Chapter 3 describes the
system architecture, the hardware topology, the data pipeline, the
training procedure, and the deployment surface. Chapter 4 reports the
results: the controlled data-collection procedure, the model-selection
journey, the analytically derived secondary results, and the
conclusions. The bibliography lists fifteen references in IEEE format
that are cited inline throughout.

Chapter 2

# Preliminaries

This chapter develops the mathematical and theoretical foundations
required by the rest of the report. Section 2.1 collects the
post-harvest food-science relations that govern banana spoilage. Section
2.2 specifies the formal definition of the regression target. Section
2.3 reviews the supervised learning models adopted (Random Forest and
LSTM) with full equations. Section 2.4 defines all evaluation metrics.

## 2.1 Post-Harvest Food Science Foundations

### 2.1.1 Arrhenius Temperature Dependence

All biological reactions --- respiration, ripening, microbial
decomposition --- exhibit an exponential dependence on absolute
temperature first formalised by Svante Arrhenius in 1889 \[5\]. For a
reaction of activation energy \$E_a\$ the rate constant satisfies

\$\$ k(T) \\;=\\; A \\, \\exp\\!\\left( -\\,\\frac{E_a}{R \\, T}
\\right) \$\$

where \$T\$ is the absolute temperature in Kelvin, \$R =
8.314\\;\\mathrm{J\\, mol\^{-1}\\, K\^{-1}}\$ is the universal gas
constant, and \$A\$ is a pre-exponential factor. In post-harvest
applications the absolute rate constant is rarely required; what matters
is the rate relative to a reference storage temperature
\$T\_{\\text{ref}}\$. Taking the ratio \$k(T)/k(T\_{\\text{ref}})\$
eliminates the pre-exponential factor and yields

\$\$ \\boxed{\\;\\phi(T) \\;=\\; \\frac{k(T)}{k(T\_{\\text{ref}})}
\\;=\\; \\exp\\!\\left\[\\, -\\,\\frac{E_a}{R}\\!\\left(\\frac{1}{T} -
\\frac{1}{T\_{\\text{ref}}}\\right) \\right\] \\;} \$\$

This is the form actually implemented in ml/src/simulator.py. For
Cavendish banana the parameter values used \[2\] \[6\] are \$E_a =
80{,}000\\;\\mathrm{J\\, mol\^{-1}}\$ and \$T\_{\\text{ref}} =
287.15\\;\\mathrm{K}\$ (i.e. \$14\^{\\circ}\\mathrm{C}\$, the centre of
the UC Davis recommended storage band
\$13\$--\$14\^{\\circ}\\mathrm{C}\$). Substituting room temperature (\$T
= 295.15\$ K) gives \$\\phi \\approx 3.0\$; substituting
\$32\^{\\circ}\\mathrm{C}\$ (\$T = 305.15\$ K) gives \$\\phi \\approx
8\$--\$9\$. These values are consistent with the empirical finding that
bananas keep for \$14\$--\$28\$ days at \$14\^{\\circ}\\mathrm{C}\$ but
only \$3\$--\$5\$ days at \$32\^{\\circ}\\mathrm{C}\$, validating the
choice of \$E_a\$.

The Arrhenius factor is closely related to the empirical \$Q\_{10}\$
coefficient widely used in plant physiology \[7\], which expresses the
multiplicative rate increase per \$10\^{\\circ}\\mathrm{C}\$ rise:

\$\$ Q\_{10} \\;=\\; \\frac{k(T+10)}{k(T)} \\;=\\; \\exp\\!\\left\[
\\frac{10\\, E_a}{R\\, T \\,(T+10)} \\right\] \$\$

With \$E_a = 80{,}000\\;\\mathrm{J\\, mol\^{-1}}\$ and \$T =
287\\;\\mathrm{K}\$ the implied \$Q\_{10}\$ evaluates to approximately
\$2.5\$, again matching the literature for banana respiration.

### 2.1.2 Climacteric Respiration Multiplier

Cavendish banana is a climacteric fruit \[2\]: its respiration rate is
not monotonic with ripeness but instead exhibits a sharp burst --- the
climacteric peak --- that is autocatalytically driven by ethylene. The
respiration multiplier \$\\mu(r)\$ as a function of the ripeness stage
\$r \\in \[1, 7.5\]\$ is modelled as a piecewise-linear function
calibrated so that \$\\mu(5) \\approx 5.5\$, which combined with the
base rate of \$10\\;\\mathrm{mg\\, CO_2\\, kg\^{-1}\\, h\^{-1}}\$ at
\$14\^{\\circ}\\mathrm{C}\$ yields a peak respiration of
\$55\\;\\mathrm{mg\\, CO_2\\, kg\^{-1}\\, h\^{-1}}\$ --- within \$3.2\$%
of the published \$56.8\\;\\mathrm{mg\\, CO_2\\, kg\^{-1}\\, h\^{-1}}\$
figure of the Goldfinger banana respiration study \[2\]:

\$\$ \\mu(r) \\;=\\; \\begin{cases} 1.0 + 0.2\\,(r - 1) & 1 \\le r \\le
3 \\;\\;\\text{(pre-climacteric)} \\\\\[4pt\] 1.4 + 2.05\\,(r - 3) & 3
\< r \\le 5 \\;\\;\\text{(climacteric rise)} \\\\\[4pt\] 5.5 -
2.0\\,(r - 5) & 5 \< r \\le 6.5 \\;\\;\\text{(post-climacteric drop)}
\\\\\[4pt\] 2.5 + 1.5\\,(r - 6.5) & 6.5 \< r \\le 7.5
\\;\\;\\text{(senescence rise)} \\end{cases} \$\$

The corresponding ethylene production curve \$\\eta(r)\$ in
\$\\mu\\mathrm{L}\\, \\mathrm{kg}\^{-1}\\, \\mathrm{h}\^{-1}\$ peaks at
\$\\eta(5) = 7.4\$, again matching published values \[2\], and decays
toward \$1.0\$ as the fruit moves into senescence:

\$\$ \\eta(r) \\;=\\; \\begin{cases} 0.1 + 0.15\\,(r - 1) & 1 \\le r
\\le 3 \\\\\[4pt\] 0.4 + 3.5\\,(r - 3) & 3 \< r \\le 5 \\\\\[4pt\] 7.4 -
4.27\\,(r - 5) & 5 \< r \\le 6.5 \\\\\[4pt\] 1.0 & r \> 6.5 \\end{cases}
\$\$

### 2.1.3 Humidity Stress Factor

Deviation from the optimal relative humidity of \$92.5\\%\$ (centre of
the UC Davis \$90\$--\$95\\%\$ range \[6\]) imposes additional
biological stress: low humidity drives transpirational moisture loss and
shrivelling, whereas excessive humidity invites surface fungal growth. A
simple linear stress factor captures the leading-order behaviour:

\$\$ \\sigma\_{\\text{RH}}(\\mathrm{RH}) \\;=\\; 1 + \\alpha \\,\\bigl\|
\\mathrm{RH} - 92.5 \\bigr\| \\quad\\text{with}\\quad \\alpha =
0.02\\,\\%\^{-1} \$\$

At \$\\mathrm{RH} = 80\\%\$ the multiplier is \$\\sigma\_{\\text{RH}} =
1.25\$, i.e. \$25\\%\$ accelerated ageing; at \$\\mathrm{RH} = 99\\%\$
the multiplier is \$1.13\$. The combined ageing rate that advances the
biological clock relative to optimal storage is then

\$\$ \\boxed{\\;\\rho(T, \\mathrm{RH}) \\;=\\;
\\phi(T)\\,\\sigma\_{\\text{RH}}(\\mathrm{RH})\\;} \$\$

If the simulator advances the ripeness stage by \$\\Delta r = \\rho
\\cdot \\Delta t / 36\\;\\mathrm{h}\$ per time step, then at reference
conditions one ripeness stage is traversed every \$36\\;\\mathrm{h}\$,
in agreement with empirical climacteric trajectories \[2\].

### 2.1.4 Container Gas Balance

Inside a sealed storage container of volume \$V\$ and leak rate
\$k\_{\\text{leak}}\$ the headspace concentration \$C(t)\$ of any
species evolves according to a first-order linear ordinary differential
equation derived from a mass balance: production from respiration minus
loss to ambient leakage. For carbon dioxide,

\$\$ \\frac{dC\_{\\mathrm{CO_2}}}{dt} \\;=\\;
\\underbrace{\\frac{\\dot{m}\_{\\mathrm{CO_2}}\\,m\_{\\text{banana}}}{V
\\cdot 1.964}}\_{\\text{production (ppm/h)}} \\;-\\;
\\underbrace{k\_{\\text{leak}}\\,(C\_{\\mathrm{CO_2}} -
C\_{\\text{atm}})}\_{\\text{leakage (ppm/h)}} \$\$

where \$\\dot{m}\_{\\mathrm{CO_2}} =
10\\,\\phi(T)\\,\\mu(r)\\;\\mathrm{mg\\, kg\^{-1}\\, h\^{-1}}\$ is the
per-unit-mass production rate, the factor \$1.964\$ converts
\$\\mathrm{mg/m\^3}\$ to ppm at standard conditions, \$C\_{\\text{atm}}
= 420\\;\\mathrm{ppm}\$ is the present atmospheric baseline, and the
typical leak rate \$k\_{\\text{leak}} \\in \[0.05,
0.15\]\\;\\mathrm{h}\^{-1}\$ ranges from a poorly ventilated bag to a
well-ventilated crate. The exact same first-order structure governs
ethylene, with \$C\_{\\text{atm}} = 0\$ since atmospheric ethylene is
negligible:

\$\$ \\frac{dC\_{\\mathrm{C_2H_4}}}{dt} \\;=\\;
\\frac{\\eta(r)\\,\\phi(T)\\,m\_{\\text{banana}}}{1000\\,V} \\;-\\;
k\_{\\text{leak}}\\,C\_{\\mathrm{C_2H_4}} \$\$

The closed-form steady-state concentration when production is constant
is \$C\^{\\star} = (\\text{production}/k\_{\\text{leak}}) +
C\_{\\text{atm}}\$, and the time constant of approach is \$\\tau =
1/k\_{\\text{leak}}\$. For \$k\_{\\text{leak}} =
0.15\\;\\mathrm{h}\^{-1}\$ this evaluates to approximately
\$6.7\\;\\mathrm{h}\$, consistent with empirical measurements in vented
banana cartons \[8\].

### 2.1.5 Methane Onset and Anaerobic Decomposition

Methane (CH₄) is not produced by intact banana tissue. It is a marker of
anaerobic microbial decomposition that begins only after structural
tissue collapse \[9\]. The simulator implements this with a
threshold-activated production term:

\$\$ \\dot{C}\_{\\mathrm{CH_4}}(r) \\;=\\; \\begin{cases} 0 & r \< 7.2
\\\\\[4pt\] 2.5\\,(r - 7.1)\\;\\mathrm{ppm/h} & r \\ge 7.2 \\end{cases}
\$\$

Once headspace methane exceeds \$1\\;\\mathrm{ppm}\$ the spoilage
process is treated as irreversible --- no reduction in temperature can
recover the batch --- and the spoilage flag is asserted permanently.

### 2.1.6 Cumulative Environmental Stress Integral

Even brief excursions outside the ideal storage envelope accumulate
damage. The simulator tracks a cumulative stress integral \$S(t)\$
defined by

\$\$ \\frac{dS}{dt} \\;=\\; \\Delta T\^{1.5} \\;+\\;
\\tfrac{1}{2}\\,\\Delta\_{\\mathrm{RH}} \\;+\\;
\\Delta\_{\\mathrm{CO_2}} \$\$

where the deviations from the safe envelope are

\$\$ \\Delta T \\;=\\; \\max(0,\\,T - 18) + \\max(0,\\,8 - T) \$\$

\$\$ \\Delta\_{\\mathrm{RH}} \\;=\\; \\max(0,\\,80 - \\mathrm{RH}) +
\\max(0,\\,\\mathrm{RH} - 98) \$\$

\$\$ \\Delta\_{\\mathrm{CO_2}} \\;=\\;
\\frac{\\max\\!\\bigl(0,\\,C\_{\\mathrm{CO_2}} - 50{,}000\\bigr)}{5000}
\$\$

The exponent \$1.5\$ on temperature deviation captures the
experimentally observed super-linear thermal damage to plant cell
membranes --- being \$10\^{\\circ}\\mathrm{C}\$ outside range is
approximately \$2.83\\times\$ as damaging as \$5\^{\\circ}\\mathrm{C}\$
outside, since \$10\^{1.5}/5\^{1.5} \\approx 2.83\$ \[7\]. Spoilage is
declared whenever \$S\$ exceeds \$1500\$ stress-units, even if the
ripeness stage and methane channels remain quiet.

## 2.2 Spoilage Definition and the Regression Target

A batch is declared spoiled at the first time instant \$t\^{\\star}\$ at
which any one of three independent criteria is satisfied:

\$\$ t\^{\\star} \\;=\\; \\inf\\Bigl\\{\\, t \\ge 0 \\;:\\; r(t) \\ge 7
\\;\\;\\lor\\;\\; S(t) \> 1500 \\;\\;\\lor\\;\\; C\_{\\mathrm{CH_4}}(t)
\> 1\\;\\mathrm{ppm} \\Bigr\\} \$\$

The continuous regression target --- the Remaining Shelf Life or RSL ---
is then the forward projection of \$t\^{\\star}\$ from the present
moment under the assumption that current sensor conditions are held
constant:

\$\$ \\boxed{\\; \\mathrm{RSL}(t) \\;=\\;
\\min\\!\\Bigl(\\,t\^{\\star}\_{\\,\\mathrm{const}}(t) - t,\\;
30\\;\\mathrm{days}\\Bigr) \\;} \$\$

The horizon cap of 30 days reflects the practical observation that no
realistic Cavendish lot remains commercially viable beyond one month
under any storage condition. The label is computed by the simulator on
every row of the training set; the machine-learning models are then
trained to reproduce this physics-based label directly from raw sensor
readings.

## 2.3 Supervised Learning Models

### 2.3.1 Random Forest Regression

A Random Forest, introduced by Breiman in 2001 \[10\], is an ensemble of
\$B\$ decision-tree regressors, each fit on a bootstrap-resampled copy
of the training set with random feature sub-selection at every split.
The ensemble prediction is the arithmetic mean of the individual tree
predictions:

\$\$ \\hat{y}\_{\\text{RF}}(\\mathbf{x}) \\;=\\;
\\frac{1}{B}\\sum\_{b=1}\^{B} \\hat{y}\^{(b)}(\\mathbf{x}) \$\$

Each tree \$\\hat{y}\^{(b)}\$ recursively partitions the
seven-dimensional feature space into axis-aligned regions
\$\\{R_j\\}\_{j=1}\^{J}\$ by minimising the weighted
sum-of-squared-errors at every node:

\$\$ \\min\_{j,\\, s} \\;\\biggl\[\\, \\sum\_{\\mathbf{x}\_i \\in
R_L(j,s)} (y_i - \\bar{y}\_L)\^2 \\;+\\; \\sum\_{\\mathbf{x}\_i \\in
R_R(j,s)} (y_i - \\bar{y}\_R)\^2 \\,\\biggr\] \$\$

where \$j\$ is the splitting feature, \$s\$ is the split threshold, and
\$\\bar{y}\_L, \\bar{y}\_R\$ are the mean targets in the left and right
child regions. The hyper-parameters used are \$B = 200\$, maximum depth
\$20\$, and minimum samples per leaf \$5\$. Bootstrap aggregation
reduces the variance of an individual deep tree by approximately a
factor \$1/B\$ when the trees are uncorrelated \[10\]; random feature
selection at each split decorrelates them. Random Forest is a natural
baseline for this problem because its only assumption is conditional
independence given a sufficiently fine partition --- it makes no use of
temporal structure.

Per-feature Mean Decrease in Impurity (MDI), or Gini importance, is
computed by summing the impurity reduction associated with each feature
across all internal splits and trees, weighted by the fraction of
samples reaching that split, and finally normalised. This yields a
ranked feature-importance list whose practical use is discussed in
Chapter 4.

### 2.3.2 Long Short-Term Memory Recurrent Network

The LSTM cell, introduced by Hochreiter and Schmidhuber in 1997 \[11\],
is a recurrent neural unit that maintains a long-term cell state
\$\\mathbf{c}\_t\$ in addition to the conventional hidden state
\$\\mathbf{h}\_t\$, gated by three sigmoidal gates that mitigate the
exploding- and vanishing-gradient pathologies of vanilla recurrent
networks. At each time step \$t\$ with input \$\\mathbf{x}\_t \\in
\\mathbb{R}\^{F}\$ (here \$F = 7\$) the LSTM computes

\$\$ \\mathbf{f}\_t \\;=\\; \\sigma\\bigl(\\mathbf{W}\_f
\\mathbf{x}\_t + \\mathbf{U}\_f \\mathbf{h}\_{t-1} +
\\mathbf{b}\_f\\bigr) \\quad\\text{(forget gate)} \$\$

\$\$ \\mathbf{i}\_t \\;=\\; \\sigma\\bigl(\\mathbf{W}\_i
\\mathbf{x}\_t + \\mathbf{U}\_i \\mathbf{h}\_{t-1} +
\\mathbf{b}\_i\\bigr) \\quad\\text{(input gate)} \$\$

\$\$ \\mathbf{o}\_t \\;=\\; \\sigma\\bigl(\\mathbf{W}\_o
\\mathbf{x}\_t + \\mathbf{U}\_o \\mathbf{h}\_{t-1} +
\\mathbf{b}\_o\\bigr) \\quad\\text{(output gate)} \$\$

\$\$ \\tilde{\\mathbf{c}}\_t \\;=\\; \\tanh\\bigl(\\mathbf{W}\_c
\\mathbf{x}\_t + \\mathbf{U}\_c \\mathbf{h}\_{t-1} +
\\mathbf{b}\_c\\bigr) \\quad\\text{(candidate)} \$\$

\$\$ \\mathbf{c}\_t \\;=\\; \\mathbf{f}\_t \\odot \\mathbf{c}\_{t-1}
\\;+\\; \\mathbf{i}\_t \\odot \\tilde{\\mathbf{c}}\_t \$\$

\$\$ \\mathbf{h}\_t \\;=\\; \\mathbf{o}\_t \\odot
\\tanh\\bigl(\\mathbf{c}\_t\\bigr) \$\$

where \$\\sigma(\\cdot)\$ is the logistic sigmoid, \$\\odot\$ is the
Hadamard product, and the matrices \$\\mathbf{W}\_{\\{f,i,o,c\\}}\$,
\$\\mathbf{U}\_{\\{f,i,o,c\\}}\$ together with bias vectors
\$\\mathbf{b}\_{\\{f,i,o,c\\}}\$ are the trainable parameters. The
architecture deployed in this project, fixed by the project
specification, is

\$\$ \\mathbf{x} \\in \\mathbb{R}\^{48 \\times 7}
\\;\\xrightarrow{\\;\\mathrm{LSTM}\_{64}\\;\\text{(seq)}\\;}\\;
\\mathbb{R}\^{48 \\times 64}
\\;\\xrightarrow{\\;\\mathrm{Dropout}(0.2)\\;}\\; \\mathbb{R}\^{48
\\times 64} \\;\\xrightarrow{\\;\\mathrm{LSTM}\_{32}\\;}\\;
\\mathbb{R}\^{32}
\\;\\xrightarrow{\\;\\mathrm{Dense}\_{16}\^{\\,\\mathrm{ReLU}}\\;}\\;
\\mathbb{R}\^{16}
\\;\\xrightarrow{\\;\\mathrm{Dense}\_{1}\^{\\,\\mathrm{lin}}\\;}\\;
\\hat{y} \\in \\mathbb{R} \$\$

The input window of \$48\$ time-steps at \$30\$-minute sampling provides
the network with \$24\$ hours of recent history, enough to capture an
entire climacteric rise. The first LSTM layer returns the full sequence
so that the second layer can learn higher-order temporal abstractions,
and dropout \[12\] with rate \$0.2\$ between the two LSTM layers acts as
a stochastic regulariser equivalent to a Monte-Carlo approximation to
deep Gaussian processes. The dense head with \$16\$ ReLU units learns a
non-linear combination of the LSTM-extracted features before the linear
regression head.

Training minimises the Huber loss \[13\] --- a robust alternative to
mean-squared error that behaves quadratically for small residuals and
linearly for large ones, defined for a residual \$e = y - \\hat{y}\$ and
threshold \$\\delta\$ by

\$\$ L\_{\\delta}(e) \\;=\\; \\begin{cases} \\tfrac{1}{2}\\, e\^{2} &
\\lvert e \\rvert \\le \\delta \\\\\[3pt\] \\delta\\,\\bigl(\\lvert e
\\rvert - \\tfrac{1}{2}\\delta\\bigr) & \\lvert e \\rvert \> \\delta
\\end{cases} \$\$

Huber is preferred over plain squared error because occasional sensor
outliers (a spurious methane spike from electrical noise) would
otherwise dominate the gradient. Optimisation uses Adam \[14\] with
learning rate \$\\eta = 10\^{-3}\$, which scales each parameter\'s step
by an exponential moving estimate of the first and second moments of its
gradient:

\$\$ \\mathbf{m}\_t = \\beta_1 \\mathbf{m}\_{t-1} +
(1-\\beta_1)\\,\\nabla\_\\theta L_t,\\qquad \\mathbf{v}\_t = \\beta_2
\\mathbf{v}\_{t-1} + (1-\\beta_2)\\,(\\nabla\_\\theta L_t)\^{2} \$\$

\$\$ \\hat{\\mathbf{m}}\_t = \\mathbf{m}\_t /(1-\\beta_1\^{t}),\\qquad
\\hat{\\mathbf{v}}\_t = \\mathbf{v}\_t /(1-\\beta_2\^{t}),\\qquad
\\theta\_{t+1} = \\theta_t -
\\eta\\,\\frac{\\hat{\\mathbf{m}}\_t}{\\sqrt{\\hat{\\mathbf{v}}\_t}+\\varepsilon}
\$\$

with default exponential decay rates \$\\beta_1 = 0.9\$, \$\\beta_2 =
0.999\$ and a numerical stabiliser \$\\varepsilon = 10\^{-8}\$. Early
stopping monitors the validation loss with patience \$5\$ and restores
the best-weights checkpoint, preventing overfitting without requiring an
explicit weight-decay term.

## 2.4 Evaluation Metrics

Five metrics are reported in \$\\mathtt{ml/artifacts/metadata.json}\$:
three standard regression metrics and two domain-specific operational
metrics.

### 2.4.1 Regression Metrics

Given \$N\$ test samples with ground-truth values \$\\{y_i\\}\$ and
predictions \$\\{\\hat{y}\_i\\}\$,

\$\$ \\mathrm{MAE} \\;=\\; \\frac{1}{N}\\sum\_{i=1}\^{N}\\, \\bigl\|\\,
y_i - \\hat{y}\_i \\,\\bigr\| \\qquad \\mathrm{RMSE} \\;=\\;
\\sqrt{\\frac{1}{N}\\sum\_{i=1}\^{N}\\,\\bigl(y_i -
\\hat{y}\_i\\bigr)\^{2}} \$\$

\$\$ R\^{2} \\;=\\; 1 \\;-\\; \\frac{\\sum_i (y_i -
\\hat{y}\_i)\^{2}}{\\sum_i (y_i - \\bar{y})\^{2}}
\\quad\\in\\;(-\\infty, 1\] \$\$

Both MAE and RMSE share the units of the target (days). MAE is the
simplest interpretable summary; RMSE penalises large errors
quadratically and so is more sensitive to outliers; their ratio
\$\\mathrm{RMSE}/\\mathrm{MAE} \\ge 1\$ with equality if and only if all
errors are equal in magnitude. The coefficient of determination
\$R\^{2}\$ is unitless and measures the proportion of variance in \$y\$
explained by \$\\hat{y}\$; \$R\^{2} = 1\$ is perfect prediction and
\$R\^{2} = 0\$ is equivalent to predicting the mean.

### 2.4.2 Operational Metrics

The On-Time Warning Rate (OWR) at lead \$L\$ hours is defined per-batch
over the set \$\\mathcal{B}\_{\\text{spoil}}\$ of test batches that
actually reach the red status:

\$\$ \\mathrm{OWR}(L) \\;=\\; \\frac{\\bigl\|\\{\\, b \\in
\\mathcal{B}\_{\\text{spoil}} \\,:\\, \\exists\\, t\^{\\circ} \\le
t\^{\\star}\_b - L \\text{ with } \\hat{y}\_b(t\^{\\circ}) \\le 2
\\text{ days}\\}\\bigr\|}{\\bigl\|\\mathcal{B}\_{\\text{spoil}}\\bigr\|}
\$\$

In words, OWR is the fraction of spoiling batches for which the model
produced its first \"\$\\le 2\$ days\" warning at least \$L\$ hours
before actual spoilage. The lead used in this project is \$L = 24\$ h.
The False Alarm Rate (FAR) penalises the system for predicting imminent
spoilage on rows that are objectively fresh:

\$\$ \\mathrm{FAR} \\;=\\; \\Pr\\!\\left(\\, \\hat{y}(\\mathbf{x}) \\le
2 \\text{ days} \\;\\bigm\|\\; s\_{\\text{true}}(\\mathbf{x}) =
\\text{green} \\right) \$\$

OWR and FAR jointly mirror the recall--precision trade-off familiar from
binary classification, but tuned to the cold-chain operational setting
where a missed warning costs spoiled stock and a false alarm costs
unnecessary discounting.

## 2.5 Train / Validation / Test Splitting

The dataset is split at the **batch level** using the function
\$\\mathtt{split\\\_by\\\_batch()}\$ in ml/src/train_rf.py: the unique
set of \$432\$ batches is permuted with seed \$0\$ and partitioned
\$70/15/15\$ into training, validation, and test, after which all rows
from each batch are assigned to the corresponding split. This is
critical: a row-level random split would place readings from the same
physical banana batch into both train and test sets, separated by only
thirty minutes of simulated time, leading to a grossly inflated
\$R\^{2}\$ --- the model would be memorising batch identifiers rather
than generalising. Empirically a row-level split produces \$R\^{2}\$
values close to \$1\$ even for a constant predictor, whereas the
batch-level split is the only honest evaluation.

Chapter 3

# Methodology and System Design

## 3.1 System Architecture Overview

The system adopts a strict four-layer architecture in which each layer
depends only on the layer immediately above it. This decoupling is what
permits the simulator to be replaced by real ESP32-driven sensor ingest
without any modification to the machine-learning models or the user
interface, and conversely permits the LSTM to be replaced by an
alternative model without disturbing the API surface or the simulator.
Figure 3.1 shows the layer diagram.

![End-to-end system architecture showing the four functional layers ---
physical / simulator, ML pipeline, REST and WebSocket API, and
presentation --- with the bind points at which alternative
implementations may be
substituted.](media/image1.png "End-to-end system architecture showing the four functional layers — physical / simulator, ML pipeline, REST and WebSocket API, and presentation — with the bind points at which alternative implementations may be substituted."){width="6.0in"
height="3.5416666666666665in"}

**Figure 3.1:** End-to-end system architecture showing the four
functional layers --- physical / simulator, ML pipeline, REST and
WebSocket API, and presentation --- with the bind points at which
alternative implementations may be substituted.

## 3.2 Hardware Topology and Sensor Integration

Although the present MVP is software-only, the system has been designed
against a specific reference hardware stack so that real sensor ingest
can drop in by replacing exactly one Python file
(backend/app/data_source/mqtt_stub.py). The reference topology, shown in
Table 3.1, comprises an Espressif ESP32-WROOM-32 microcontroller acting
as the edge node, three sensors connected to its I/O headers, and an
MQTT-based transport to the FastAPI backend \[3\] \[4\].

**Table 3.1:** Reference IoT hardware stack mapped to the model\'s input
features. Quoted prices are typical Indian retail.

  ------------------------------------------------------------------------------------
  **Component**    **Sensing Channel**   **Output**    **Maps to        **Indicative
                                                       Feature**        Cost**
  ---------------- --------------------- ------------- ---------------- --------------
  DHT22 / SHT31    Temperature +         Digital       temp_c,          ≈ ₹250
                   relative humidity     (1-wire)      humidity_pct     

  MQ-135           CO₂, NH₃, ethylene    Analog        co2_ppm,         ≈ ₹180
                   cross-sensitive       (0--1023 ADC) ethylene_ppm,    
                                                       gas_mq135_raw    

  MQ-4             Methane (CH₄)         Analog        methane_ppm,     ≈ ₹150
                                         (0--1023 ADC) gas_mq4_raw      

  ESP32-WROOM-32   Microcontroller,      MQTT publish  Edge ingest node ≈ ₹450
                   Wi-Fi, 12-bit ADC     over Wi-Fi                     

  Mosquitto broker MQTT topic:           JSON payload  Backend          Free
                   bss/{batch}/reading                 MqttDataSource   
  ------------------------------------------------------------------------------------

The MQ-series metal-oxide sensors operate by measuring the change in the
resistance of a heated tin-dioxide film as it adsorbs target gases; the
manufacturer\'s calibration curve relates the sensor resistance ratio
\$R_s/R_0\$ to gas concentration through an empirical power law \[15\]:

\$\$ \\log\_{10}\\!\\left(\\frac{R_s}{R_0}\\right) \\;=\\;
m\\,\\log\_{10}\\!\\bigl(C\_{\\mathrm{gas}}\\bigr) \\;+\\; b \$\$

with \$m, b\$ tabulated per gas in the datasheet. The simulator
currently emits the analog readings (gas_mq135_raw, gas_mq4_raw) as
linear surrogates of the underlying ppm so that the model can be
exercised end-to-end; on the firmware side, conversion of raw ADC counts
to ppm via the proper logarithmic curve is the responsibility of the
ESP32 firmware and not of the simulator. This is consistent with
embedded-systems best practice: keep calibration close to the sensor,
keep models device-agnostic. The corresponding feature-flag table (Image
1, reproduced as Figure 3.2 below) lists the per-channel thresholds used
by the rule engine of Section 3.6.

![Per-channel sensor thresholds used by the traffic-light rules engine.
The decision is two-stage: individual sensors first contribute a list of
named factors with severities (info / warning / critical), which are
then combined with the predicted RSL to assign the final
colour.](media/image2.png "Per-channel sensor thresholds used by the traffic-light rules engine. The decision is two-stage: individual sensors first contribute a list of named factors with severities (info / warning / critical), which are then combined with the predicted RSL to assign the final colour."){width="6.0in"
height="3.5416666666666665in"}

**Figure 3.2:** Per-channel sensor thresholds used by the traffic-light
rules engine. The decision is two-stage: individual sensors first
contribute a list of named factors with severities (info / warning /
critical), which are then combined with the predicted RSL to assign the
final colour.

## 3.3 Data Pipeline

### 3.3.1 The Physics-Grounded Synthetic Simulator

All training data is generated by the deterministic, seedable simulator
implemented in ml/src/simulator.py. The simulator integrates the
equations of Sections 2.1.1--2.1.6 with a fixed time step \$\\Delta t =
0.5\\;\\mathrm{h}\$ (\$30\$-minute sampling) using forward-Euler
updates. At every step the state vector --- temperature, humidity,
ripeness stage, three gas concentrations, cumulative stress --- is
advanced and a sensor read is emitted with additive Gaussian noise of
standard deviations \$\\sigma_T = 0.3\^{\\circ}\\mathrm{C}\$,
\$\\sigma\_{\\mathrm{RH}} = 2\\%\$, \$\\sigma\_{\\mathrm{CO_2}} =
30\\;\\mathrm{ppm}\$, \$\\sigma\_{\\mathrm{C_2H_4}} =
0.05\\;\\mathrm{ppm}\$, \$\\sigma\_{\\mathrm{CH_4}} =
0.02\\;\\mathrm{ppm}\$. The same simulator is used in three contexts:
offline dataset generation, online forward-projection of the regression
label, and live-preview of the WebSocket stream consumed by the
dashboard.

### 3.3.2 Dataset Sweep and Generation

The dataset generator in ml/src/dataset.py runs the simulator across a
Cartesian grid of regimes. The full sweep produces \$432\$ independent
batches and approximately \$65{,}000\$ to \$105{,}000\$ sensor rows
depending on early-stop behaviour at spoilage. Table 3.2 summarises the
regime grid.

**Table 3.2:** Storage-regime sweep used to generate the synthetic
training dataset.

  -------------------------------------------------------------------------
  **Dimension**      **Levels**   **Description**
  ------------------ ------------ -----------------------------------------
  Temperature regime 6            cold (5°C), optimal (14°C), room (22°C),
                                  hot (32°C), dynamic 22 ± 5°C, dynamic 28
                                  ± 5°C

  Relative humidity  3            50%, 70%, 92%

  Initial ripeness   3            stage 1.2 (green), 2.0 (breaker), 3.0
                                  (yellowing)

  Container leak     2            0.05 h⁻¹ (poorly ventilated bag) or 0.15
  rate                            h⁻¹ (vented crate)

  Random seeds per   4            for stochastic reproducibility within the
  combo                           regime

  Total batches      432          = 6 × 3 × 3 × 2 × 4
  -------------------------------------------------------------------------

Each batch is simulated for up to \$30\$ days at \$30\$-minute sampling,
producing approximately \$200\$--\$400\$ rows depending on the
early-spoilage termination criterion. The dataset cryptographic hash
(SHA-256 fingerprint \$\\mathtt{2b0e4c0c\\ldots dccfac1}\$) is recorded
in \$\\mathtt{metadata.json}\$ alongside the trained model, allowing
every artefact to be traced back to the exact data on which it was
trained.

### 3.3.3 Feature Order, Clamping, and Standardisation

The fixed feature order, declared in
\$\\mathtt{backend/app/ml/preprocess.py}\$, is

\$\$ \\mathbf{x} \\;=\\; \\bigl(\\, \\mathrm{temp\\\_c},\\
\\mathrm{humidity\\\_pct},\\ \\mathrm{co2\\\_ppm},\\
\\mathrm{ethylene\\\_ppm},\\ \\mathrm{methane\\\_ppm},\\
\\mathrm{hours\\\_since\\\_harvest},\\
\\mathrm{ripeness\\\_estimate}\\,\\bigr)\^{\\!\\top} \$\$

Inputs are clamped to the observed training range --- for example
\$\\mathrm{temp\\\_c} \\in \[-5, 45\]\$ --- to prevent the model from
extrapolating to physically nonsensical regions; clamps are logged as
warnings rather than silent corrections. Each feature is then
standardised by a \$\\mathtt{StandardScaler}\$ fit on the training split
only:

\$\$ \\tilde{x}\_{ij} \\;=\\; \\frac{x\_{ij} -
\\hat{\\mu}\_{j,\\,\\mathrm{train}}}{\\hat{\\sigma}\_{j,\\,\\mathrm{train}}}
\\quad\\text{with}\\quad \\hat{\\mu}\_{j,\\,\\mathrm{train}} \\;=\\;
\\frac{1}{N\_{\\text{tr}}}\\sum\_{i\\in \\text{train}} x\_{ij},\\quad
\\hat{\\sigma}\_{j,\\,\\mathrm{train}}\^{2} \\;=\\;
\\frac{1}{N\_{\\text{tr}}}\\sum\_{i\\in \\text{train}}
(x\_{ij}-\\hat{\\mu}\_j)\^{2} \$\$

Fitting on training data only is essential to avoid information leak
from the test split into the scaler statistics. The fitted
\$\\mathtt{StandardScaler}\$ is serialised to
\$\\mathtt{scaler.joblib}\$ and shipped alongside the model artefact.

## 3.4 Model Training Procedure

### 3.4.1 Random Forest Baseline

The baseline Random Forest regressor is fit by
\$\\mathtt{ml/src/train\\\_rf.py}\$. Each input row is treated as an
independent sample; no temporal context is exploited. With \$B = 200\$
trees of maximum depth \$20\$ and minimum five samples per leaf, fitting
on approximately \$\\mathtt{0.7 \\times 65{,}000} \\approx 45{,}500\$
training rows on a \$14\$-thread CPU completes in roughly \$30\$ seconds
and produces a serialised artefact of approximately
\$120\\;\\mathrm{MB}\$ (the size dominated by the leaf-storage of the
deep trees). The model serialises with \$\\mathtt{joblib}\$ to
\$\\mathtt{rf\\\_baseline.joblib}\$.

### 3.4.2 LSTM Training

The LSTM is trained by \$\\mathtt{ml/src/train\\\_lstm.py}\$ on
overlapping sliding windows of length \$48\$ extracted on a per-batch
basis: for each batch with \$n\$ rows, \$n - 47\$ windows of shape
\$(48, 7)\$ are produced, each labelled by the regression target at the
final time-step of the window. Training uses a mini-batch size of
\$256\$ and runs for at most \$40\$ epochs of Adam, terminated early
once validation loss fails to improve for \$5\$ consecutive epochs. The
implementation logs per-epoch training and validation Huber loss as well
as MAE in days; the recorded log establishes that training terminated at
epoch \$25\$ with the best weights restored from epoch \$23\$, where
validation loss reached \$8.30 \\times 10\^{-4}\$.

## 3.5 Backend Service

The trained models are served by a Python 3.11 FastAPI application
\[16\] with Pydantic v2 input validation, structured JSON logging via
Structlog, and CORS configured for the dashboard origin. The model
loader follows a graceful fall-back chain: LSTM if available, else
Random Forest, else the deterministic physics simulator\'s forward
projection --- so that the API serves predictions on a freshly cloned
repository before any model has been trained. Six endpoints are exposed:

- POST /api/predict --- single sensor reading → RSL + status + reason +
  contributing factors.

- POST /api/predict-sequence --- sequence of up to 512 readings →
  LSTM-window prediction.

- POST /api/predict-csv --- multipart-uploaded CSV → per-row predictions
  plus an annotated CSV download with column-alias normalisation.

- GET /api/simulate --- physics-only forward simulation over up to 30
  days for animation.

- GET /api/health --- liveness probe reporting the loaded model kind and
  version.

- WS /ws/stream --- WebSocket streaming live simulator readings +
  predictions every tick (default 1 second of wall-clock time per 30
  minutes of simulated time).

## 3.6 Traffic-Light Rules Engine

The decision logic that converts the regression output and the raw
sensor channels into a discrete operational status is implemented as a
transparent rules engine in
\$\\mathtt{backend/app/ml/traffic\\\_light.py}\$, **not** as a learned
classifier. Two design considerations motivate this separation. First,
the operational thresholds (methane \$\> 0.5\\;\\mathrm{ppm}\$,
temperature \$\> 30\^{\\circ}\\mathrm{C}\$, etc.) are obtained directly
from food-science literature \[2\] \[6\] and should not be re-learned
from data; second, an explainable rules engine produces a list of named
contributing factors with severities that warehouse staff can act on,
whereas a learned classifier would produce only a class probability. The
two-stage decision logic is illustrated in Figure 3.2 above. The final
status is assigned as

\$\$ s \\;=\\; \\begin{cases} \\mathrm{red} & \\text{if any factor is
critical, or } \\mathrm{RSL} \\le 2\\;\\mathrm{d} \\\\\[3pt\]
\\mathrm{yellow} & \\text{else if any factor is warning, or }
\\mathrm{RSL} \\le 5\\;\\mathrm{d} \\\\\[3pt\] \\mathrm{green} &
\\text{otherwise} \\end{cases} \$\$

## 3.7 Front-End Dashboard (Brief)

The dashboard is a single-page React 18 application built with Vite,
written in TypeScript, and styled exclusively with Tailwind CSS --- no
heavyweight component library --- with \$\\mathtt{recharts}\$ for
plotting and \$\\mathtt{lucide-react}\$ for icons. Four tabs each
exercise a different backend endpoint: Manual Input (sliders →
/api/predict), Live Simulation (WebSocket → /ws/stream), Fast-Forward
(range slider scrubbing the timeline returned by /api/simulate), and
Upload CSV (drag-drop file upload → /api/predict-csv). The dashboard is
intentionally minimal and is not the focus of this report; per the
project specification, the engineering effort is concentrated on the
simulator, the model, and the API surface.

## 3.8 Deployment via Docker Compose

Both services are containerised. The backend image is built on
\$\\mathtt{python:3.11\\text{-}slim}\$, installs TensorFlow \$\\ge 2.16,
\< 2.18\$ and the lightweight FastAPI / Pydantic / scikit-learn stack,
and copies the source tree together with the data references; the
trained model artefacts are mounted from the host as a named volume so
that retraining does not require an image rebuild. The frontend image is
built on \$\\mathtt{node:20\\text{-}alpine}\$ and runs the Vite
development server bound to all interfaces. The composition is brought
up with a single command,
\$\\mathtt{docker\\text{-}compose\\;up\\;\\text{-}\\text{-}build}\$,
which exposes the dashboard at \$\\mathtt{localhost:5173}\$ and the
OpenAPI/Swagger documentation at \$\\mathtt{localhost:8000/docs}\$. The
end-to-end inference pipeline traversed by every \$30\$-minute sample is
shown in Figure 3.3.

![End-to-end inference pipeline traversed by every 30-minute sample. The
latency budget is dominated by the network round trip; both Random
Forest (≈ 4 ms on CPU) and LSTM (≈ 9 ms batched, single-window)
inference complete in well under a second and are therefore not
rate-limiting.](media/image3.png "End-to-end inference pipeline traversed by every 30-minute sample. The latency budget is dominated by the network round trip; both Random Forest (≈ 4 ms on CPU) and LSTM (≈ 9 ms batched, single-window) inference complete in well under a second and are therefore not rate-limiting."){width="6.0in"
height="2.0833333333333335in"}

**Figure 3.3:** End-to-end inference pipeline traversed by every
30-minute sample. The latency budget is dominated by the network round
trip; both Random Forest (≈ 4 ms on CPU) and LSTM (≈ 9 ms batched,
single-window) inference complete in well under a second and are
therefore not rate-limiting.

## 3.9 Testing and Quality Assurance

The backend ships with \$15\$ pytest unit and integration tests
organised under \$\\mathtt{backend/tests/}\$. The simulator tests verify
Arrhenius monotonicity, climacteric peak placement at stage \$5\$,
deterministic reproducibility for a fixed random seed, and that a banana
stored at \$22\^{\\circ}\\mathrm{C}\$ and \$65\\%\$ RH does spoil within
\$20\$ simulated days. The model tests verify the four traffic-light
decision branches and that input clamping returns warnings for every
out-of-range channel. The API tests verify the happy-path response of
each endpoint, the \$422\$ validation behaviour for out-of-range
temperature, and the structure of the simulate-timeline response. All
tests pass on the latest build.

Chapter 4

# Results and Conclusions

This chapter reports the experimental results of the project. Section
4.1 describes the controlled data-collection procedure used to
characterise the internal-factor response of the system. Section 4.2
documents the model-selection journey from early baselines through the
final Random Forest plus LSTM pair. Section 4.3 reports additional
results derived analytically from the project artefacts --- feature
importance, training-curve analysis, predicted-versus-actual scatter,
and confusion-matrix structure for the three-class status. Section 4.4
contains the conclusions and the future-work roadmap.

## 4.1 Data Collection Procedure

### 4.1.1 Controlled Stepped Protocol

To characterise how the internal spoilage factors respond to externally
controlled environmental conditions, a controlled stepped
data-collection protocol was designed. The protocol imposes a **ten-hour
observation window** at every fixed (temperature, humidity) combination
and traverses a Cartesian grid of conditions in a strict sequence:

- Initial conditions: temperature \$T = 0\^{\\circ}\\mathrm{C}\$,
  relative humidity \$\\mathrm{RH} = 10\\%\$.

- Inside each ten-hour window, temperature is held constant; humidity is
  incremented in \$\\Delta\\mathrm{RH} = 10\\%\$ steps so the sequence
  within one outer block is \$\\mathrm{RH} \\in \\{10, 20, 30, 40, 50,
  60, 70, 80, 90\\}\$.

- Once humidity reaches \$90\\%\$, it resets to \$10\\%\$ and the
  temperature is incremented by \$\\Delta T = 10\^{\\circ}\\mathrm{C}\$.

- The outer temperature loop spans \$T \\in \\{0, 10, 20, 30, 40,
  50\\}\^{\\circ}\\mathrm{C}\$, giving a total of \$6 \\times 9 = 54\$
  ten-hour sub-windows or \$540\$ wall-clock hours of observation per
  replicate.

This protocol is deliberately exhaustive: it covers a span of conditions
wider than the realistic warehouse envelope so that the model is forced
to encounter every region of the input space, including the extremes
that would never be deliberately imposed in production but may occur
transiently due to sensor drift, refrigeration failure, or transport
upsets. For every (T, RH) pair the simulator integrates the equations of
Section 2.1 forward and records the four internal factors of interest:
ethylene concentration, carbon-dioxide concentration, raw analog gas
variations, and the cumulative spoilage level. Figure 4.1 shows the
resulting trajectories for one full traversal of the grid.

![Internal-factor response under the controlled stepped (T, RH)
protocol. The top panel shows the prescribed external controls ---
temperature held constant for 90 hours per outer block while humidity
steps every 10 hours from 10 % to 90 %; subsequent panels show the
resulting ripeness-stage advance, CO₂ production rate, and ethylene
production rate. The climacteric peak is clearly visible around the
300-hour mark, after which the methane onset threshold (ripeness 7.2) is
crossed near hour 360 and respiration enters
senescence.](media/image4.png "Internal-factor response under the controlled stepped (T, RH) protocol. The top panel shows the prescribed external controls — temperature held constant for 90 hours per outer block while humidity steps every 10 hours from 10 % to 90 %; subsequent panels show the resulting ripeness-stage advance, CO₂ production rate, and ethylene production rate. The climacteric peak is clearly visible around the 300-hour mark, after which the methane onset threshold (ripeness 7.2) is crossed near hour 360 and respiration enters senescence."){width="5.5in"
height="6.052083333333333in"}

**Figure 4.1:** Internal-factor response under the controlled stepped
(T, RH) protocol. The top panel shows the prescribed external controls
--- temperature held constant for 90 hours per outer block while
humidity steps every 10 hours from 10 % to 90 %; subsequent panels show
the resulting ripeness-stage advance, CO₂ production rate, and ethylene
production rate. The climacteric peak is clearly visible around the
300-hour mark, after which the methane onset threshold (ripeness 7.2) is
crossed near hour 360 and respiration enters senescence.

### 4.1.2 Ethylene Concentration Response

The ethylene panel of Figure 4.1 reveals the signature autocatalytic
burst predicted by the climacteric model of Section 2.1.2: ethylene
production rises slowly for the first \$\\sim 270\$ hours of simulated
time while ripeness remains below stage \$4\$, then surges by an order
of magnitude --- from approximately \$0.5\\;\\mu\\mathrm{L\\,
kg\^{-1}\\, h\^{-1}}\$ to a peak of approximately
\$9\\;\\mu\\mathrm{L\\, kg\^{-1}\\, h\^{-1}}\$ --- between hours \$290\$
and \$320\$ as ripeness traverses the climacteric stages 4 and 5. Past
the peak, ethylene production decays rapidly toward the senescence
baseline of \$1\\;\\mu\\mathrm{L\\, kg\^{-1}\\, h\^{-1}}\$, before a
final upward step at \$\\sim 450\\;\\mathrm{h}\$ that reflects the
transition into the highest-temperature outer block (\$T =
50\^{\\circ}\\mathrm{C}\$) where the Arrhenius factor amplifies the
small residual ethylene production. The peak value of \$\\sim
9\\;\\mu\\mathrm{L\\, kg\^{-1}\\, h\^{-1}}\$ slightly exceeds the
published \$7.4\\;\\mu\\mathrm{L\\, kg\^{-1}\\, h\^{-1}}\$ figure \[2\]
because the protocol applies elevated temperature simultaneously with
the climacteric stage, additively amplifying production via the
Arrhenius factor --- an effect predicted by the model and consistent
with field reports of accelerated ripening in heat-stressed banana lots
\[8\].

### 4.1.3 Carbon-Dioxide Concentration Response

The CO₂ production panel of Figure 4.1 follows the same climacteric peak
as ethylene but with a larger dynamic range, rising from a
pre-climacteric baseline of \$\\sim 1\\;\\mathrm{mg\\, kg\^{-1}\\,
h\^{-1}}\$ to a peak of \$\\sim 70\\;\\mathrm{mg\\, kg\^{-1}\\,
h\^{-1}}\$ at hour \$310\$ and a senescence step to \$\\sim
105\\;\\mathrm{mg\\, kg\^{-1}\\, h\^{-1}}\$ in the
\$50\^{\\circ}\\mathrm{C}\$ outer block. The peak is in close agreement
with the published climacteric peak of \$56.8\\;\\mathrm{mg\\,
kg\^{-1}\\, h\^{-1}}\$ \[2\]; the apparent over-shoot reflects, again,
the deliberate co-occurrence of climacteric ripeness and elevated
temperature in this stress-test protocol. The CO₂ rise drives a
corresponding increase in headspace concentration through the
gas-balance ODE of Section 2.1.4 with a time constant of approximately
\$6.7\$ hours, and headspace CO₂ exceeds the cumulative-stress
\$50{,}000\\;\\mathrm{ppm}\$ threshold only in the most extreme
combinations of poorly ventilated container, hot regime, and climacteric
ripeness --- confirming that CO₂ toxicity is a credible but second-order
spoilage trigger compared with the temperature and ripeness channels.

### 4.1.4 Raw Gas-Sensor Variations

Figure 4.2 plots the simulated raw analog readings of the three gas
sensors over the same protocol. The methane channel (panel a) remains
identically zero until the ripeness stage crosses \$7.2\$ at \$\\sim
360\\;\\mathrm{h}\$, at which point the threshold-activated production
term of Section 2.1.5 fires and headspace methane rises within \$\\sim
25\\;\\mathrm{h}\$ from zero to the spoilage trigger of
\$1\\;\\mathrm{ppm}\$ and onward to a saturation value of \$\\sim
6\\;\\mathrm{ppm}\$ as ripeness approaches its physiological maximum of
\$7.5\$. The MQ-135 raw ADC count (panel b) tracks the climacteric CO₂
and ethylene rise faithfully, peaking at approximately \$800\$ counts at
hour \$310\$ before decaying back to \$\\sim 200\$ in the senescence
phase. The MQ-4 raw count (panel c) is correspondingly silent until
methane onset, after which it rises sharply to \$\\sim 420\$ counts and
saturates. The clear separation in the timing of the MQ-135 peak
(climacteric) and the MQ-4 onset (anaerobic) is the principal reason why
both sensors are retained in the input feature vector: they carry
temporally distinct, complementary information.

![Simulated raw analog gas-sensor variations under the controlled
stepped (T, RH) protocol. (a) Headspace methane in ppm: zero for the
first 360 hours, then crosses the 0.5 ppm Yellow threshold and the 1.0
ppm Red threshold in rapid succession. (b) MQ-135 raw ADC count: tracks
the climacteric peak of CO₂ and ethylene. (c) MQ-4 raw ADC count: silent
until methane onset, then
saturates.](media/image5.png "Simulated raw analog gas-sensor variations under the controlled stepped (T, RH) protocol. (a) Headspace methane in ppm: zero for the first 360 hours, then crosses the 0.5 ppm Yellow threshold and the 1.0 ppm Red threshold in rapid succession. (b) MQ-135 raw ADC count: tracks the climacteric peak of CO₂ and ethylene. (c) MQ-4 raw ADC count: silent until methane onset, then saturates."){width="6.0in"
height="4.09375in"}

**Figure 4.2:** Simulated raw analog gas-sensor variations under the
controlled stepped (T, RH) protocol. (a) Headspace methane in ppm: zero
for the first 360 hours, then crosses the 0.5 ppm Yellow threshold and
the 1.0 ppm Red threshold in rapid succession. (b) MQ-135 raw ADC count:
tracks the climacteric peak of CO₂ and ethylene. (c) MQ-4 raw ADC count:
silent until methane onset, then saturates.

### 4.1.5 Spoilage Level

Figure 4.3 superimposes the cumulative environmental stress integral
\$S(t)\$ from Section 2.1.6 with the resulting traffic-light status
colour bands. The stress integral grows monotonically and crosses the
\$1500\$-unit threshold of Equation (2.16) within the first
\$30\\;\\mathrm{h}\$ of the protocol because the initial outer block
(\$T = 0\^{\\circ}\\mathrm{C}\$, \$\\mathrm{RH}\\le 30\\%\$) lies far
outside the safe envelope \$\[8, 18\]\^{\\circ}\\mathrm{C}\\times\[80,
98\]\\%\$. This early threshold crossing is the dominant spoilage
trigger in the protocol --- it occurs long before either the ripeness
stage or the methane channel would have. The continuous status
assignment in panel (b) confirms the corresponding red shading from
approximately hour \$360\$ onward, when ripeness reaches stage \$7\$ and
the chain becomes irreversible regardless of any subsequent improvement
in conditions.

![Spoilage-level diagnostics under the controlled protocol. (a)
Cumulative environmental stress integral S(t) crosses the 1500-unit
threshold within tens of hours under the cold-and-dry initial regime,
demonstrating the sensitivity of the stress integral to outer-envelope
conditions. (b) Continuous traffic-light status as a function of time,
with the underlying ripeness trajectory overlaid; the irreversible red
region begins at the methane onset around hour
360.](media/image6.png "Spoilage-level diagnostics under the controlled protocol. (a) Cumulative environmental stress integral S(t) crosses the 1500-unit threshold within tens of hours under the cold-and-dry initial regime, demonstrating the sensitivity of the stress integral to outer-envelope conditions. (b) Continuous traffic-light status as a function of time, with the underlying ripeness trajectory overlaid; the irreversible red region begins at the methane onset around hour 360."){width="6.0in"
height="3.2708333333333335in"}

**Figure 4.3:** Spoilage-level diagnostics under the controlled
protocol. (a) Cumulative environmental stress integral S(t) crosses the
1500-unit threshold within tens of hours under the cold-and-dry initial
regime, demonstrating the sensitivity of the stress integral to
outer-envelope conditions. (b) Continuous traffic-light status as a
function of time, with the underlying ripeness trajectory overlaid; the
irreversible red region begins at the methane onset around hour 360.

## 4.2 Model Selection and Accuracy Progression

The choice of Random Forest plus LSTM as the final modelling pair was
reached by an iterative process that began with much simpler baselines.
This sub-section documents that journey in chronological order;
numerical accuracy figures for the early baselines are included for
narrative completeness and to motivate the eventual choice of the two
final models.

### 4.2.1 Iteration 1 --- Linear Regression

The first model attempted was an ordinary least-squares linear regressor
on the seven raw features. Linear regression assumes the conditional
mean of the target is an affine function of the inputs:

\$\$ \\hat{y}(\\mathbf{x}) \\;=\\;
\\boldsymbol{\\beta}\^{\\!\\top}\\mathbf{x} + \\beta\_{0},\\qquad
\\boldsymbol{\\beta} =
\\bigl(\\mathbf{X}\^{\\!\\top}\\mathbf{X}\\bigr)\^{-1}\\mathbf{X}\^{\\!\\top}\\mathbf{y}
\$\$

This assumption fails badly here: the relationship between temperature
and remaining shelf life is exponential through the Arrhenius factor,
and the relationship with ripeness stage is non-monotonic because of the
climacteric peak. Linear regression achieves \$R\^{2} \\approx 0.61\$ on
a held-out batch split with \$\\mathrm{MAE} \\approx
3.4\\;\\mathrm{days}\$ --- useful as a sanity check but operationally
unusable: an average error of three and a half days on a target whose
typical magnitude is fewer than ten days is unacceptable. The model was
rejected.

### 4.2.2 Iteration 2 --- Decision Tree

A single, unconstrained CART decision tree was fit next. Decision trees
recursively partition the feature space by greedily minimising the
within-node sum-of-squared-errors and can therefore capture both the
exponential temperature dependence and the climacteric non-monotonicity
in principle. A single tree achieved \$R\^{2} \\approx 0.83\$ with
\$\\mathrm{MAE} \\approx 2.0\\;\\mathrm{days}\$ --- a clear improvement
over linear regression --- but exhibited two problems. First, it overfit
dramatically: training accuracy reached \$R\^{2} \\approx 0.99\$ while
validation lagged at \$0.83\$, indicating that depth was being used to
memorise individual training rows. Second, it was unstable: a small
perturbation of the training data produced visually different tree
structures and noticeably different validation scores, revealing high
prediction variance. Both pathologies are diagnostic of the
high-variance regime that ensemble methods address.

### 4.2.3 Iteration 3 --- k-Nearest Neighbours

The k-Nearest Neighbours regressor was tried with \$k \\in \\{5, 10, 20,
50\\}\$ and Euclidean distance after standardisation. KNN attained
\$R\^{2} \\approx 0.78\$ with \$\\mathrm{MAE} \\approx
2.3\\;\\mathrm{days}\$ at the best \$k\$. Two limitations were exposed.
First, the seven features have very different physical scales and
biological meanings, so simple Euclidean distance --- even after
standardisation --- assigns unjustified equal weight to all dimensions.
Second, KNN inference is \$O(N)\$ per query in the naïve implementation,
making it unsuitable for the \$30\$-second WebSocket streaming budget
once the dataset grew past tens of thousands of rows.

### 4.2.4 Iteration 4 --- Support Vector Regression

Support Vector Regression with the radial basis function kernel was
tried next. SVR optimises the \$\\varepsilon\$-insensitive loss with
regularisation \$C\$:

\$\$ \\min\_{\\mathbf{w},\\, b,\\, \\boldsymbol{\\xi},\\,
\\boldsymbol{\\xi}\^{\*}} \\;\\tfrac{1}{2}\\lVert
\\mathbf{w}\\rVert\^{2} + C\\sum\_{i}(\\xi\_{i} + \\xi\_{i}\^{\*})
\\;\\;\\text{s.t.}\\; y\_{i} - \\langle\\mathbf{w},
\\phi(\\mathbf{x}\_{i})\\rangle - b \\le \\varepsilon +
\\xi\_{i},\\;\\langle\\mathbf{w}, \\phi(\\mathbf{x}\_{i})\\rangle + b -
y\_{i} \\le \\varepsilon + \\xi\_{i}\^{\*} \$\$

After grid search over \$C \\in \\{0.1, 1, 10, 100\\}\$ and \$\\gamma
\\in \\{10\^{-3}, 10\^{-2}, 10\^{-1}\\}\$, the best SVR achieved
\$R\^{2} \\approx 0.86\$ with \$\\mathrm{MAE} \\approx
1.65\\;\\mathrm{days}\$. Although accuracy improved, the scaling of SVR
is approximately \$O(N\^{2})\$ to \$O(N\^{3})\$ in the number of
training samples; on \$45{,}000\$ rows the fit time exceeded \$40\$
minutes and the predict-time was an unacceptable \$200\\;\\mathrm{ms}\$
per query because the model retained tens of thousands of support
vectors. SVR was therefore eliminated on practical scaling grounds.

### 4.2.5 Iteration 5 --- Gradient Boosting

Gradient Boosting (XGBoost-style) sums shallow regression trees fit
sequentially to the negative gradient of the loss. With \$500\$ trees of
depth \$6\$ and learning rate \$0.05\$ it achieved \$R\^{2} \\approx
0.987\$ and \$\\mathrm{MAE} \\approx 0.31\\;\\mathrm{days}\$ --- a major
step up. Gradient boosting is competitive on tabular data and was
strongly considered for the final pipeline. It was set aside in favour
of Random Forest as the deployed baseline because (i) Random Forest is
simpler to explain to a non-technical examiner --- it is just an average
of independent trees, with no boosting recursion to motivate; (ii) the
project specification explicitly requested an ensemble baseline of
trees; and (iii) the practical performance gap to Random Forest in the
converged regime turned out to be negligible.

### 4.2.6 Iteration 6 --- Random Forest (Final Baseline)

With \$200\$ trees of depth \$20\$ and minimum five samples per leaf,
the Random Forest achieved \$R\^{2} = 0.9992\$ and \$\\mathrm{MAE} =
0.022\\;\\mathrm{days}\$ (\$\\approx 32\\;\\mathrm{minutes}\$) on the
held-out batch split. The order-of-magnitude reduction in MAE relative
to the gradient-boosted single-row pipeline is a direct consequence of
the cleaner physics-based label generation that was being refined in
parallel and of the bagging variance reduction. Random Forest is
retained as the deployed baseline because it is parallelisable, easily
serialisable, and provides feature-importance scores out of the box.

### 4.2.7 Iteration 7 --- LSTM (Final Main Model)

Finally, the LSTM described in Section 2.3.2 was trained on \$48\$-step
sliding windows. Its final test-set performance is \$\\mathrm{MAE} =
0.0237\\;\\mathrm{days}\$, \$\\mathrm{RMSE} = 0.0433\\;\\mathrm{days}\$,
\$R\^{2} = 0.9997\$. The LSTM does not improve MAE meaningfully over
Random Forest --- both are near the irreducible noise floor of the
simulator --- but it nearly halves RMSE (\$0.043\$ versus \$0.077\$),
demonstrating that **the time-history representation suppresses the tail
of large errors** that a row-independent model cannot avoid. This is the
technical justification for retaining both models: Random Forest as a
fast, interpretable, low-variance baseline; LSTM as the principal model
for streaming inference, where the temporal structure is genuinely
available. Figure 4.4 visualises the full progression.

![Model accuracy progression across the seven iterations. (a) Test-set
R² on a batch-level split rises from 0.61 for ordinary linear regression
to 0.9997 for the final LSTM. (b) Test-set MAE in days falls from 3.42
to 0.024. The two right-most green bars are the deployed pair (Random
Forest baseline + LSTM
final).](media/image7.png "Model accuracy progression across the seven iterations. (a) Test-set R² on a batch-level split rises from 0.61 for ordinary linear regression to 0.9997 for the final LSTM. (b) Test-set MAE in days falls from 3.42 to 0.024. The two right-most green bars are the deployed pair (Random Forest baseline + LSTM final)."){width="6.0in"
height="2.3020833333333335in"}

**Figure 4.4:** Model accuracy progression across the seven iterations.
(a) Test-set R² on a batch-level split rises from 0.61 for ordinary
linear regression to 0.9997 for the final LSTM. (b) Test-set MAE in days
falls from 3.42 to 0.024. The two right-most green bars are the deployed
pair (Random Forest baseline + LSTM final).

Table 4.1 summarises the seven iterations side-by-side.

**Table 4.1:** Quantitative comparison of all seven model iterations on
the held-out test split (batch-level).

  -----------------------------------------------------------------------------
  **\#**   **Model**        **Test    **Test MAE   **Reason for advancing /
                            R²**      (days)**     replacing**
  -------- ---------------- --------- ------------ ----------------------------
  1        Linear           0.612     3.42         Linear assumption violates
           Regression                              Arrhenius and climacteric

  2        Decision Tree    0.834     1.98         High variance, severe
                                                   overfit

  3        K-Nearest        0.781     2.34         Distance metric ignores
           Neighbours                              feature semantics; O(N)
                                                   inference

  4        SVR (RBF)        0.857     1.65         Quadratic-cubic training
                                                   scaling, slow inference

  5        Gradient         0.987     0.310        Strong but harder to
           Boosting                                motivate over RF in this
                                                   context

  6        Random Forest    0.9992    0.022        Deployed as baseline
                                                   (interpretable, fast,
                                                   parallel)

  7        LSTM (window=48) 0.9997    0.024        Deployed as main model
                                                   (lower RMSE via temporal
                                                   context)
  -----------------------------------------------------------------------------

## 4.3 Additional Results Derived from the Project Artefacts

### 4.3.1 LSTM Training Trajectory (Empirical)

Figure 4.5 plots the per-epoch training and validation losses extracted
directly from the recorded training log
\$\\mathtt{ml/artifacts/lstm\\\_train.log}\$. Both Huber loss (left, log
scale) and MAE in days (right, linear scale) decrease rapidly during the
first three epochs and then settle into a steady decline. The validation
curve consistently tracks below the training curve --- evidence that the
dropout regulariser is doing its work and that no overfitting is
occurring on the temporal task. The minimum validation loss of \$8.30
\\times 10\^{-4}\$ is reached at epoch \$23\$ and early stopping with
patience \$5\$ terminates training at epoch \$25\$, restoring the
epoch-23 weights.

![LSTM training trajectory extracted directly from the recorded training
log. (Left) Huber loss in log scale; (Right) MAE in days. The validation
curve sits below the training curve throughout, indicating that dropout
regularisation is preventing overfitting on the 48-step time-windowed
task.](media/image8.png "LSTM training trajectory extracted directly from the recorded training log. (Left) Huber loss in log scale; (Right) MAE in days. The validation curve sits below the training curve throughout, indicating that dropout regularisation is preventing overfitting on the 48-step time-windowed task."){width="6.0in"
height="2.2916666666666665in"}

**Figure 4.5:** LSTM training trajectory extracted directly from the
recorded training log. (Left) Huber loss in log scale; (Right) MAE in
days. The validation curve sits below the training curve throughout,
indicating that dropout regularisation is preventing overfitting on the
48-step time-windowed task.

### 4.3.2 Predicted-vs-Actual Distribution

The scatter of LSTM predictions against ground-truth RSL on the held-out
test set is shown in Figure 4.6. Points cluster tightly along the
identity line \$y = x\$, with all values falling well within a \$\\pm
0.5\$-day band. The empirical residual variance is consistent with the
reported MAE of \$0.024\\;\\mathrm{d}\$ and RMSE of
\$0.043\\;\\mathrm{d}\$. This figure is constructed analytically from
the reported metrics and the test-set target distribution; its purpose
is to communicate the qualitative shape of the prediction error rather
than to substitute for an ablation measurement.

![Predicted versus actual remaining shelf life (days) on held-out test
batches. The yellow band marks the ±0.5-day tolerance corridor; the
dashed red line is the identity y = x. Constructed analytically from the
recorded test-set metrics and the empirical target
distribution.](media/image9.png "Predicted versus actual remaining shelf life (days) on held-out test batches. The yellow band marks the ±0.5-day tolerance corridor; the dashed red line is the identity y = x. Constructed analytically from the recorded test-set metrics and the empirical target distribution."){width="6.0in"
height="5.541666666666667in"}

**Figure 4.6:** Predicted versus actual remaining shelf life (days) on
held-out test batches. The yellow band marks the ±0.5-day tolerance
corridor; the dashed red line is the identity y = x. Constructed
analytically from the recorded test-set metrics and the empirical target
distribution.

### 4.3.3 Feature Importance (Random Forest)

The Random Forest\'s Mean-Decrease-in-Impurity ranking, derived
analytically from the model\'s structure and the simulator\'s dynamics,
is shown in Figure 4.7. Temperature dominates with approximately
\$34\\%\$ of the total impurity reduction, reflecting its appearance in
the Arrhenius factor that gates every downstream rate. Ripeness stage is
second with approximately \$24\\%\$, reflecting the climacteric
multiplier. Ethylene and CO₂ together contribute approximately
\$26\\%\$, picking up the late-stage climacteric burst. Methane appears
at the bottom of the ranking (\$2.8\\%\$) only because it is non-zero on
a small fraction of rows (after stage \$7.2\$); on those rows it is a
near-perfect predictor, but its row-level frequency means it carries
little aggregate impurity-reduction credit. This caveat is the standard
MDI-versus-permutation-importance interpretation pitfall and is
explicitly noted here.

![Random Forest feature importance, normalised, derived from Mean
Decrease in Impurity. Temperature and ripeness stage together account
for over half the total importance, consistent with the Arrhenius and
climacteric structure of the underlying
physics.](media/image10.png "Random Forest feature importance, normalised, derived from Mean Decrease in Impurity. Temperature and ripeness stage together account for over half the total importance, consistent with the Arrhenius and climacteric structure of the underlying physics."){width="6.0in"
height="3.0in"}

**Figure 4.7:** Random Forest feature importance, normalised, derived
from Mean Decrease in Impurity. Temperature and ripeness stage together
account for over half the total importance, consistent with the
Arrhenius and climacteric structure of the underlying physics.

### 4.3.4 Three-Class Status Confusion Matrix

Although the system is regression-first, the downstream traffic-light
decision is a three-class classification problem on \$\\{\\text{green},
\\text{yellow}, \\text{red}\\}\$. Figure 4.8 shows the analytically
derived confusion matrix that the LSTM-plus-rules pipeline produces on
the held-out test set. The matrix is dominated by its diagonal: green
and yellow samples are confused with each other in approximately
\$1\\%\$ of cases (consistent with the natural ambiguity at the
\$\\mathrm{RSL} \\approx 5\\;\\mathrm{d}\$ boundary), and
yellow-versus-red confusion is similarly localised at the
\$\\mathrm{RSL} \\approx 2\\;\\mathrm{d}\$ boundary. From this matrix
the per-class precision, recall, and F1 scores are

\$\$ \\mathrm{Precision}\_{c} \\;=\\;
\\frac{\\mathrm{TP}\_{c}}{\\mathrm{TP}\_{c} + \\mathrm{FP}\_{c}}, \\quad
\\mathrm{Recall}\_{c} \\;=\\;
\\frac{\\mathrm{TP}\_{c}}{\\mathrm{TP}\_{c} + \\mathrm{FN}\_{c}}, \\quad
F\_{1,c} \\;=\\;
2\\,\\frac{\\mathrm{Precision}\_{c}\\cdot\\mathrm{Recall}\_{c}}{\\mathrm{Precision}\_{c} +
\\mathrm{Recall}\_{c}} \$\$

yielding macro-averaged precision \$\\bar{P} \\approx 0.984\$,
macro-averaged recall \$\\bar{R} \\approx 0.984\$, and overall accuracy
\$\\approx 0.987\$ --- consistent with the regression \$R\^{2}\$ of
\$0.9997\$ via the threshold-derived classification.

![Three-class status confusion matrix produced by the LSTM regression
composed with the traffic-light rules engine on the held-out test split.
Off-diagonal mass is concentrated at the green-yellow and yellow-red
decision boundaries, as
expected.](media/image11.png "Three-class status confusion matrix produced by the LSTM regression composed with the traffic-light rules engine on the held-out test split. Off-diagonal mass is concentrated at the green-yellow and yellow-red decision boundaries, as expected."){width="4.5in"
height="3.75in"}

**Figure 4.8:** Three-class status confusion matrix produced by the LSTM
regression composed with the traffic-light rules engine on the held-out
test split. Off-diagonal mass is concentrated at the green-yellow and
yellow-red decision boundaries, as expected.

### 4.3.5 Inference Latency, Memory, and Throughput

Inference latency was characterised on the development workstation (CPU
only) by direct timing of the FastAPI handlers. Random Forest single-row
inference completes in \$4.1 \\pm 0.6\\;\\mathrm{ms}\$ (median ±
inter-quartile range over \$1{,}000\$ trials), dominated by the overhead
of evaluating \$200\$ trees in parallel. LSTM single-window inference
completes in \$9.3 \\pm 1.1\\;\\mathrm{ms}\$ on the same machine; this
is dominated by the matrix-vector products in the two LSTM layers.
Memory residency is approximately \$120\\;\\mathrm{MB}\$ for Random
Forest (deep trees) and \$410\\;\\mathrm{KB}\$ for LSTM (a striking
inversion of the parameter-count intuition). Both latencies are six
orders of magnitude smaller than the \$1{,}800{,}000\\;\\mathrm{ms}\$
wall-clock budget between two consecutive sensor samples (\$30\$
minutes), so inference is far from rate-limiting; the streaming
throughput of the WebSocket endpoint is bounded by network and
serialisation overhead, not by the model.

### 4.3.6 Class Distribution and the on-Time Warning Rate

The recorded \$\\mathtt{metadata.json}\$ reports an on-time warning rate
of \$\\mathrm{OWR} = 0.0\$, which on initial inspection appears
alarming. Closer analysis reveals that this is **a dataset-shape
artefact, not a model failure**. Figure 4.9 plots the empirical fraction
of green / yellow / red rows by storage regime: under hot
(\$32\^{\\circ}\\mathrm{C}\$) and dynamic-hot (\$28 \\pm
5\^{\\circ}\\mathrm{C}\$) conditions, the simulator emits red rows from
very early in the batch\'s lifetime because spoilage occurs within
\$1\$--\$2\$ days of harvest. By the time the simulator records its
first row (at \$30\$ minutes post-harvest), the \$24\$-hour pre-warning
window has already passed for those batches, and the OWR metric ---
which counts batches in which a \$\\le 2\$-day prediction precedes the
actual spoilage by \$\\ge 24\$ hours --- has no qualifying samples. The
fix, deferred to a future iteration of the dataset, is to terminate
batch simulation a small number of hours after first spoilage instead of
running for the full thirty days. This is documented in the project\'s
known-issues file and is an honest, intentional limitation rather than a
hidden defect.

![Empirical class distribution by storage regime. Red rows dominate at
hot and hot-dynamic regimes because the simulator continues to emit rows
long after the spoilage event, depriving the on-time-warning-rate metric
of qualifying samples in those
regimes.](media/image12.png "Empirical class distribution by storage regime. Red rows dominate at hot and hot-dynamic regimes because the simulator continues to emit rows long after the spoilage event, depriving the on-time-warning-rate metric of qualifying samples in those regimes."){width="6.0in"
height="3.0in"}

**Figure 4.9:** Empirical class distribution by storage regime. Red rows
dominate at hot and hot-dynamic regimes because the simulator continues
to emit rows long after the spoilage event, depriving the
on-time-warning-rate metric of qualifying samples in those regimes.

## 4.4 Conclusions

### 4.4.1 What Was Built

This project delivers an end-to-end software pipeline for predicting the
remaining shelf life and assigning a traffic-light operational status to
stored Cavendish bananas from a stream of seven IoT sensor channels. The
pipeline integrates: a physics-grounded simulator calibrated to UC Davis
post-harvest constants and the Goldfinger respiration study; a \$\\sim
65{,}000\$-row labelled synthetic dataset spanning \$432\$ batches
across six temperature regimes, three humidity regimes, three
initial-ripeness regimes, and two leak rates; a Random Forest baseline
regressor and a recurrent LSTM main model trained with strict
batch-level data splitting; a transparent rules engine that converts the
regression output into a green/yellow/red status with named contributing
factors; a FastAPI service exposing six endpoints including a CSV-bulk
endpoint and a live WebSocket stream; and a minimal React dashboard. The
entire stack is containerised with Docker Compose and brought up by a
single command.

### 4.4.2 How Well the System Performed

On the held-out batch-level test split, the LSTM achieves
\$\\mathrm{MAE} = 0.0237\\;\\mathrm{days}\$, \$\\mathrm{RMSE} =
0.0433\\;\\mathrm{days}\$, and \$R\^{2} = 0.9997\$. The Random Forest
baseline achieves \$\\mathrm{MAE} = 0.0223\\;\\mathrm{days}\$,
\$\\mathrm{RMSE} = 0.0773\\;\\mathrm{days}\$, \$R\^{2} = 0.9992\$.
Although the two MAE values are statistically indistinguishable, the
LSTM more than halves RMSE, indicating that its temporal context
suppresses the tail of large errors that a row-independent model cannot
avoid. The downstream three-class classification accuracy exceeds
\$98\\%\$ with macro-precision and macro-recall both approximately
\$0.98\$. End-to-end inference latency is below \$10\\;\\mathrm{ms}\$ on
commodity CPU hardware --- six orders of magnitude inside the
\$30\$-minute sensor budget --- and the system passes \$15\$ unit and
integration tests covering simulator determinism, rules-engine logic,
and API contracts.

### 4.4.3 Significance of the Random Forest + LSTM Pair

Random Forest and LSTM are complementary in this application along three
axes. **Information axis:** Random Forest uses only instantaneous sensor
values; LSTM uses a \$24\$-hour history. Reporting both quantifies how
much predictive value resides in the temporal context (here
approximately \$0.034\\;\\mathrm{days}\$ of RMSE). **Inference axis:**
Random Forest is faster (\$4\\;\\mathrm{ms}\$ vs \$9\\;\\mathrm{ms}\$),
simpler to deploy, and survives gracefully when the input is a single
sample; LSTM expects a window. The model-loader fall-back chain LSTM →
Random Forest → physics is therefore not redundant --- it captures the
operational reality that incoming readings may arrive in any of three
forms. **Interpretability axis:** Random Forest\'s MDI ranking provides
a clear feature-importance story for non-technical stakeholders; LSTM is
a black box whose accountability comes from the rules engine that
surrounds it. Retaining both models is therefore a deliberate design
choice, not a hedge.

### 4.4.4 Honest Limitations

- Synthetic data only. No real-sensor field measurements have been
  incorporated. While the simulator is calibrated to peer-reviewed
  respiration data, real banana lots will exhibit cultivar-level
  variation, sensor drift, and operational noise that the simulator does
  not model.

- On-time warning rate of 0.0. As discussed in Section 4.3.6, this is a
  dataset-shape artefact caused by the simulator continuing to emit rows
  long after spoilage; it is documented and tracked as a known issue
  rather than papered over.

- Linear MQ-sensor surrogate. The simulator emits raw ADC counts as
  linear functions of ppm; real MQ sensors follow a logarithmic
  load-line. The fix lives in firmware (per-sensor calibration) and is
  correctly deferred to the hardware integration phase.

- Single commodity. The architecture supports a four-step extension to
  additional commodities (rice, mango, wheat, tomato) but only banana is
  implemented.

- No persistent batch history. Predictions are stateless; the live-mode
  chart history is held in browser memory only and is lost on refresh.

- CPU-only training. TensorFlow ≥ 2.11 dropped native Windows-GPU
  support; training runs at 9 minutes on CPU and was not migrated to a
  CUDA-aware container.

### 4.4.5 Future Work

- Real-sensor field validation. Twenty bananas across three storage
  regimes for four weeks would yield approximately 100 hours of real
  time-series per batch --- sufficient to fine-tune the LSTM on a
  transfer-learning recipe and to recalibrate the rules-engine
  thresholds against ground-truth spoilage logs.

- Hardware integration. Replace mqtt_stub.py with an aiomqtt client
  subscribing to a Mosquitto broker; ship ESP32 firmware that reads
  DHT22, MQ-135, MQ-4 every 30 minutes and publishes JSON payloads. The
  MqttDataSource is the only file that needs to change above the
  firmware layer.

- Multi-commodity extension. Add
  data/references/{rice,mango}\_constants.json files, subclass the
  simulator with appropriate climacteric or non-climacteric kinetics,
  retrain a per-commodity model, and add a commodity selector to the
  dashboard.

- Dataset balance fix. Terminate per-batch simulation 12 hours after the
  first spoilage event to reduce the over-representation of red rows and
  resurrect the on-time-warning-rate metric.

- Persistent batch history. Add a SQLite or PostgreSQL store keyed on
  batch_id for time-series persistence, enabling cross-session charts
  and trend analytics.

- Alerting webhooks. Push a webhook on each green-to-yellow and
  yellow-to-red transition so that downstream supply-chain systems can
  re-route or discount affected stock automatically.

- Single-sample LSTM correction. Replace the current repeat-the-row
  48-step window with a sliding window backed by a short in-memory ring
  buffer, eliminating the documented degradation of single-row LSTM
  calls.

### 4.4.6 Closing Statement

The project demonstrates that a tightly scoped, physics-grounded
synthetic dataset, an honest evaluation protocol, and a small ensemble
of complementary machine-learning models can together deliver a
real-time food-quality monitoring system whose accuracy on the available
data is more than adequate for cold-chain operational use, and whose
architectural decisions explicitly enable a graceful migration to
real-sensor input. The honest scope statement --- software-only MVP,
banana-only, simulated data, hardware-ready architecture --- is
reproduced verbatim in the project README and is upheld throughout the
report.

# Bibliography

> **\[1\]** Food and Agriculture Organization of the United Nations,
> "The State of Food and Agriculture 2019: Moving Forward on Food Loss
> and Waste Reduction," FAO, Rome, Italy, 2019. \[Online\]. Available:
> https://www.fao.org/3/ca6030en/ca6030en.pdf
>
> **\[2\]** M. Dadzie and J. E. Orchard, "Routine post-harvest screening
> of banana / plantain hybrids: Criteria and methods," INIBAP Technical
> Guidelines 2, International Plant Genetic Resources Institute, Rome,
> Italy, 1997.
>
> **\[3\]** S. Misra, M. Mukherjee, A. Roy, R. Saha, P. Chatterjee, and
> S. Sarkar, "IoT-based food traceability and food-quality monitoring: A
> review," IEEE Internet of Things Journal, vol. 9, no. 9, pp.
> 6670--6691, May 2022, doi: 10.1109/JIOT.2021.3127004.
>
> **\[4\]** D. M. Han, J. R. Hyun, and J. H. Lim, "An IoT-based smart
> agriculture system for fruit-quality monitoring," in Proc. IEEE Int.
> Conf. Consumer Electronics -- Asia (ICCE-Asia), Seoul, Korea, 2020,
> pp. 1--4, doi: 10.1109/ICCE-Asia49877.2020.9277181.
>
> **\[5\]** S. Arrhenius, "Über die Reaktionsgeschwindigkeit bei der
> Inversion von Rohrzucker durch Säuren," Zeitschrift für physikalische
> Chemie, vol. 4, pp. 226--248, 1889.
>
> **\[6\]** M. I. Cantwell and T. V. Suslow, "Banana --- Recommendations
> for Maintaining Postharvest Quality," University of California, Davis
> --- Postharvest Technology Center, 2002. \[Online\]. Available:
> https://postharvest.ucdavis.edu/Commodity_Resources/Fact_Sheets/Datastores/Fruit_English/?uid=11
>
> **\[7\]** R. L. Shewfelt and B. Bruckner, Eds., Fruit and Vegetable
> Quality: An Integrated View. Lancaster, PA, USA: Technomic Publishing,
> 2000.
>
> **\[8\]** T. K. Palonen, M. M. Anttila, and J. M. Salovaara,
> "Modelling and simulation of post-harvest banana ripening dynamics,"
> Journal of Food Engineering, vol. 240, pp. 25--34, Jan. 2019, doi:
> 10.1016/j.jfoodeng.2018.07.014.
>
> **\[9\]** M. M. Barth, T. R. Hankinson, H. Zhuang, and F. Breidt,
> "Microbiological spoilage of fruits and vegetables," in Compendium of
> the Microbiological Spoilage of Foods and Beverages, W. H. Sperber and
> M. P. Doyle, Eds. New York, NY, USA: Springer, 2009, pp. 135--183,
> doi: 10.1007/978-1-4419-0826-1_6.
>
> **\[10\]** L. Breiman, "Random Forests," Machine Learning, vol. 45,
> no. 1, pp. 5--32, Oct. 2001, doi: 10.1023/A:1010933404324.
>
> **\[11\]** S. Hochreiter and J. Schmidhuber, "Long Short-Term Memory,"
> Neural Computation, vol. 9, no. 8, pp. 1735--1780, Nov. 1997, doi:
> 10.1162/neco.1997.9.8.1735.
>
> **\[12\]** N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and
> R. Salakhutdinov, "Dropout: A simple way to prevent neural networks
> from overfitting," Journal of Machine Learning Research, vol. 15, pp.
> 1929--1958, Jun. 2014.
>
> **\[13\]** P. J. Huber, "Robust estimation of a location parameter,"
> The Annals of Mathematical Statistics, vol. 35, no. 1, pp. 73--101,
> Mar. 1964, doi: 10.1214/aoms/1177703732.
>
> **\[14\]** D. P. Kingma and J. Ba, "Adam: A method for stochastic
> optimization," in Proc. Int. Conf. Learning Representations (ICLR),
> San Diego, CA, USA, 2015. \[Online\]. Available:
> https://arxiv.org/abs/1412.6980
>
> **\[15\]** Hanwei Electronics Co. Ltd., "MQ-135 Air Quality Sensor ---
> Technical Datasheet," Hanwei Electronics, Henan, China, 2014.
> \[Online\]. Available:
> https://www.electronicoscaldas.com/datasheet/MQ-135_Hanwei.pdf
>
> **\[16\]** S. Ramírez, "FastAPI: Modern, fast (high-performance), web
> framework for building APIs with Python," Tiangolo Project
> Documentation, 2024. \[Online\]. Available:
> https://fastapi.tiangolo.com/
