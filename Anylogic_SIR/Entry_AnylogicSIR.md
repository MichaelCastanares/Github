---
layout: default
title: Blog
---

[Home](/) | [Research Blog](/blog)

---
### "Anylogic: SEIR model"
*7 May 2025*

XXX


**Q1:** How does network structure affect the spread of disease?;

**Q2:** When is it better to use Agent-based (AB) or Differential Equation (DE) model?;

My goal is to share some insights to these questions based on the simulation model I built using AnyLogic software.

### Platform
All simulations were built and run using AnyLogic 8 Personal Learning Edition 8.9.8.


### A. Theoretical Foundations


### B. Application
I now extend our base model to incorporate the effect of negative reviews with Adoption. I introduced a new block that captures behavior of a user with negative experience.

> *Insight*. In building this models, I find that skills and creativity should go together. I need creativity to create an abstraction how the agents would work. I also need skills to translate my ideas and implement it to AnyLogic platform. It was a back-and-forth process of trying to debug and understand how different functions and parameters are setup.

WantsToBuy --> Negative User. This transition is random with 1% probability of occuring. The idea that in every 100 buyers, there is a chance 1 buyer who will have a negative review (referred to as NegativeUser).

Now this Negative User will randomly send "DontBuy" message to User and Buyers. For user, receiving a DontBuy message will discourage product use (50% probability of transition USER->BUYER). For buyer, receiving a DontBuy message will encourage a change of decision (90% probability of transition BUYER->PotentialUser).

The corresponding state chart with the negative User is shown below.
<img src="./images/Anylogic_StateChart2.png" alt="Alt text" height="300">
<img src="./images/Anylogic_Sim2.gif" alt="Alt text" height="300">

To understand the effect of negative reviews. I simulate an adversarial attack event on the system at t=180 days. At this point, I increased the Negative contact rate, the number of "DontBuy" messages sent to random agent from 2 to 7 per day. I also included a parameter DaystoResolve which captures the number of days until the attack is removed, 180 + N_daystoresolve.

From the simulation from t<180 days, the product adoption increases up to 4,000 users. At t=180 days, we can observe a large drop in USERS due to the adversarial attack. After after 280 days (180 + N_daystoresolve), we can observe that the adoption reverts back to initial level close to 4,000.

We test this for different N_daystoresolve, 100 days (red), 60 days, 15 days (green) using compare runs in AnyLogic. The resulting adoption curve converges back to initial level faster with a shorter days to resolve. This suggest that resolving the attack in shorted days limits the extent of the loss of user-engagement. Notably, we can see similar fraction of Negative Users across simulation runs.

<img src="./images/Anylogic_Sim2b.png" alt="Alt text" height="300">

I utilized python to further examine the adoption curve and extracting the area-under-the-curve (AUC). The AUC corresponds to the loss cumulative user engagement with units (N users * time). I normalized the AUC relative to the control case (AUC for DaystoResolve=1). This AUC could be used to estimate the loss in profit when users disengages with the product. 

<img src="./images/Anylogic_Results2.png" alt="Alt text" height="200">

> From the simulation, we can provide some insights for 
> 
> **Q2:** What is the impact of a negative product review?;
> 
> **A2:** A negative product review significantly impacts the adoption and cumulative user engagement particularly with the presence of highly active Negative Users (high contact rate). A 60 day resolution from the negative review attack results to 75% loss in user-engagement. Thus, this exercise provides test scenarios on the resilience of the system and highlights possible interventions to mitigate attacks

### Final thoughts
This blog demonstrates an agent-based model (ABM) of consumer market built in AnyLogic. From the simulation, I find that matching consumer wait time with the delivery time (business efficiency) affect product adoption. Extending the model the incorporate negative reviews/attacks, I find that highly active negative users decreased product adoption with the AUC as a potential metric to estimate the loss in user engagement and business profit. Overall, this highlights the usefulness of simulation models such as ABM to test scenarios and derive insights that support business profitabilty and operational resilience.


Codes used to generate the figures may be found here: [View Code Repository on GitHub](https://github.com/MichaelCastanares/Github/tree/main/Anylogic_Market)

Disclaimer of AI use: Claude Haiku was used to improve the flow of the discussion.


### Reference:
https://en.wikipedia.org/wiki/Agent-based_model

Grigoryev, I. 2025. "Anylogic 8 in three days: A quick course in simulation modeling". 6th Edition. The Anylogic Company: Chicago, IL, USA.



