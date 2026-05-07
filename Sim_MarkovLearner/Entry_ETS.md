---
layout: default
title: Blog
---

[Home](/) | [Research Blog](/blog)

---
### "Simulation: Zone of Proximal Development"
*In Progress*

Adaptive Learning

In this blog, we explore a simulation demonstrating Adaptive Learning. We build on the principle of Zone of Proximal Development by Levy Vygotsky.  


**Data**. 


### A. Theoretical Foundations
**Cognitive Load Theory (CLT)**. This framework, developed by John Sweller, suggests that learning happens when "extraneous load" (irrelevant info) is minimized and "germane load" (mental effort that builds schemas) is maximized [xx].

**Zone of Proximal Development**. A theory developed by Vygotsky which posits that learning occurs at a zone between what a student can do independently and what they cannot do at all.

**Expertise Reversal Effect**. A cognitive load theory phenomenon where instructional help designed for novices (heavy scaffolding) can hinder learning of experts (those who have prior knowledge). Experts learn more with less guidance. This suggests that instructional materials should adapt to the learners prior knowledge.


### B. Framework
Here I describe the behavior of the student and an active tutor agent in the simulation. 

The knowledge is a "Ground-Truth", $G$, adjacency matrix of Letters A to E representing idea patterns that the student must uncover. The matrix defines the next probable letter (similar to a Markov Chain transition).

The learner/student. A first-order Markov agent that uses weighted learning and suffers from an exponential forget factor. The task is to predict the next letter based on its learn representation.

The study session comprised of learning phrases/sequences. During study session, the student updates it's Markov Matrix, $M$,  comprising of the probability of transitions based on the observed phrases.

I used the Bayesian Knowledge Tracing framework (BKT) to model learning[WIKI]. BKT is an algorithm used in many Intelligent Tutoring System to model learner's mastery on given knowledge. The key parameters for the BKT model are:

- $P_i$. The probability of the student knowing the skill before hand.
- $P(T)$. The learning probability. This parameter is dynamically tuned during ZPD
- $P_{slip}$. The probability the student makes a mistake when applying a known skill.
- $P_{guess}$. The probability the student correctly applies an unknown skill (lucky guess).
- 
https://en.wikipedia.org/wiki/Bayesian_knowledge_tracing


At the start of the study, the student has its own latent BKT matrix. In this case, its a square matrix comprised of a constant.

**Update equations**. For each study phrase, the student updates is Markov Matrix of observation weighted by a forget factor.  The adjacency of the connection between state $i$ and state $j$ at time $t$ is determined by the previous weight, forget factor, and the presence of the new observation:
$$
    W_{i,j}^{(t)} = \left(\lambda \cdot W_{i,j}^{(t-1)}\right) + 1_{obs}(i,j)
$$
where $W_{i,j}$ is the weight of the adjacency matrix, $\lambda$ is the forget factor $(0 < \lambda < 1)$ and $1_{obs}(i,j)$ is the indicator function which takes the value 1 if the transition $i->j$ was observed and 0, otherwise.

The student is tasked to predict the next letter of the phrase and updates its BKT latent knowledge.

$$
P(L_{t+1}) = P(L_t|C_t) + (1-P(L_t|C_t)) \cdot P(T)
$$


**The Active tutor and ZPD Function.** We introduce an active tutor whose role is to identify the best 


The tutor selects the next set of patterns that maximizes the knowledge Gap ($\Delta$) for the current state $i$, ensuring that the material is within ZPD.

$$
    \Delta_{i,j} = |P(j|i) -\hat{P}(j|i)_{student}|
$$

The tutor's selection $S$ is 

$$
    S^{(t+1)} = argmax_{j}(\Delta_{i,j})
$$



### Final thoughts

This analysis demonstrates that while ARIMA models provide a theoretically grounded framework for time-series forecasting, simpler approaches like the Naive model often provide competitive or superior performance. The key insight is not that ARIMA should be dismissed, but rather gain intuition on how it works and why it did not work. I think the best way to learn is to be exposed with different models.

Codes used to generate the figures may be found here: [View Code Repository on GitHub](https://github.com/MichaelCastanares/Github/tree/main/TS_ARIMA)


Disclaimer of AI use: Claude Sonnet was used to improve the flow of the discussion.


### Reference:

Hyndman, R. J., & Athanasopoulos, G. (n.d.). Exponential smoothing. In Forecasting: Principles and practice (3rd ed.). Retrieved from https://otexts.com/fpppy/nbs/08-exponential-smoothing.html


