# Part 1 · Day 1 — Incubyte Culture Ways of Working & Setting Up to Build

**Date completed:** 2026-10-22 · **Time spent:** ~5 hours

## Success criteria
| Criterion (copied from the planner) | Done? | Evidence (link or section below) |
| --- | --- | --- |
| The Independent Pod page and Values in Action page on the Incubyte playbook | Yes | [Independent Pods](#independent-pods) |
| Reflection: Incubyte's six guiding principles are quality with pragmatism and extreme ownership and proactive collaboration and active pursuit of mastery and inviting giving and acting on feedback and ensuring client success - which one will stretch you most and why | Yes | [Reflection on Values](#reflection-on-values) |
| Study: the four DORA metrics applied to data work - what counts as a deployment and a change failure and a time to restore for a data pipeline | Yes | [DORA Metrics](#dora-metrics) |
| Practice: install Claude Code and the BEE and Learn plugins and run Learn on one small task | Yes | NA |
| Exercise: write a small Python function that cleans one record - trims fields and normalises a date and rejects a missing id - test-first with pytest | Yes | [Code](../code/part1/day1/) |
| Reflection: what does test-first change about how you would build a data transformation | Yes | [Reflection on Test-First Approach](../code/day1/reflection.md) |

## Key learnings
- DORA Metrics - Learnt about how we can use the DORA metrics to track the efficiency and stability of a system based on the output and problems and how to use them to course correct.
- Incubyte Guiding Princples - Learnt about the guiding principles that captains everything from work style to client communication.
- Independent Pods - Learnt about the pod structure, working methodology, characteristics, and guidelines for each pod to work efficiently and ideally.
- TDD - Learnt how to iteratively build a functionality with test-first and reflected on how this method makes any functionality developed with quite bullet proof.

## Exercises
Developed the Python function to trim fields, normalise a date, and reject any with a missing ID. Took the test-first approach using red-green-refactor to iteratively test the function and add minimal features to pass test, and overall build all the target features.

## Reflection
The values in action part was something that I had applied in my work to a certain degree, but the emphasis on feedback was something newer that I wish to apply. TDD was also something new which demonstrated how it helps me making sure the quality of the software is built from ground up, iteratively, and taking every requirement into proper consideration.

## AI use
- I used Claude Code to get an idea of how to approach a generic functionality with test-first methodology. The initial output was a bit generic, so I refined it to give me a systematic step-by-step approach.
- I also used AI to generate the README of this repository.
- Inline hinting with the Zed browser helped in writing the notes to avoid typos and grammatical mistakes.

## Open questions
NA

## Changes after review
- 2026-10-22: Restructured the submission

# Day 1 - Incubyte Culture Ways of Working & Setting Up to Build
## DORA Metrics

A set of standardized indicators that measure how effectively an enterprise builds, deploys, and operates software. They assess delivery performance across two dimensions: throughput, which measures the speed and frequency of software changes, and stability, which measures the frequency of failures and the ability to recover from them.

### Metrics

#### Throughput Metrics

Throughput is a measure of how many changes can move through the system over a period of time.

- Change Lead Time: The time it takes for a code change to go from development to production. Shorter lead times indicate faster delivery of features and fixes.
- Deployment Frequency: The number of deployments to production within a given time period. Higher deployment frequency indicates faster delivery of features and fixes.
- Failed Deployment Recovery Time: The time it takes to recover from a deployment that fails and requires immediate intervention. This metric measures the ability to quickly recover from failures and minimize downtime.

#### Stability Metrics

Instability is a measure of how well the software deployments go.

- Change Failure Rate: The ratio of deployments that require immediate intervention following a deployment. Likely resulting in a rollback of the changes or a “hotfix” to quickly remediate any issues. This metric measures the stability of the software and the effectiveness of the deployment process.
- Deployment Recovery Rate: The ratio of deployments that are unplanned but happen as a result of an incident in production. This metric measures the ability to recover from failures and minimize downtime.

### DORA in Data Pipeline Context

#### Deployment

A deployment in a data pipeline context is an identifiable change release of change to production/qa data or addition or removal of data, data source, data pipeline, or data transformation. It is a change that is deployed to production and is expected to be stable and reliable.

#### Change Failure

A change failure in the data context is a deployment that results in data becoming incorrect, incomplete, unavailable, or simple wrong. This can have a cascading effect on downstream systems, so a change failure can also be data pipelines crashing, reports or dashboards being inccorect, unavailable, or down, SLAs not being met or data being lost, or data being corrupted. So, a failure can be something that ran with green but resulted in incorrect data or a failure that resulted in a pipeline crash or data loss.

#### Time to Restore

Time to restore in the data context is the time it takes to recover from a change failure and restore the data to a correct, complete, and available state. This can consists of correction of transformation logic, schema changes, data reprocessing, syntactical corrections, configurational changes, or any other changes that are required to restore the data to a correct or expected state.

## Independent Pods

Autonomous teams at Incubyte which owns a business initiative, it acts almost as a self-managing independent business unit of its own. Each independent pod should function with minimal dependencies on the client's onshore team.

### Purpose

- Bring our clients' dreams to life by being their trusted engineering partners, crafting innovative software solutions.
- Challenge offshore development stereotypes by delivering exceptional quality and proving the value of craftsmanship.
- Empower clients to deliver value quickly and frequently to their end users.
- Ensure long-term success for our clients by building reliable, sustainable, and impactful solutions.
- Raise the bar of software craft by setting a new standard for the community.

### Characteristics of an Independent Pod

Other than the guiding principles and a clear purpose, following constitute the ideal characteristics of an Independent Pod

- **Clarity of Goals** - There should be absolute clarity about the goals of the initiative, the vision and objectives of the client, and sync of the team with the client. The efforts and direction of efforts should be align with the aim of the client
- **Team Structure** - An independent pod should be small, cohesive team, with a balance of functional and non-functional capabilities, which does not only encourage individual growth in focused and cross-functional areas, but also makes the pod self-sufficient and not dependent on externalaties.
- **Autonomous Decision Making** - There should be autonomous, swift decision-making with stakeholder input, transparent accountability, and continuous learning from mistakes.
- **Accoutability with Learning, not blaming** - There should be shared, transparent, and proactive accountability, driven by clear quality standards, collective ownership, visibility, and continuous learning without blame.
- **Clear Communication** - There should be a default-to-open culture that promotes transparent, concise, audience-appropriate, and compassionate communication while maintaining privacy for sensitive matters.
- **Feedback as a Learning Ladder** - There should be frequent, timely, multi-directional, and actionable feedback loops that foster continuous improvement, alignment, and shared team goals.

### Ideal Working Style of an Independent Pod

- **Crafting Excellence** - Craftsmanship, technical excellence, and a product mindset are the fundamental traits of an independent pod. These attributes lead to delivery of high-quality, maintainable, and user-focused solutions.
- **Building Client Trust** - Building a strong client partnership on shared ownership, a consulting mindset, and proactive, transparent communication is of utmost importance. We are their engineering partners, not just vendors or service providers.
- **Enabling Mastery and Growth** - A culture of continuous improvement, self-driven learning, and knowledge sharing strengthens individual and collective expertise. 
- **Ensuring Team Health**- There should be a supportive and psychologically safe environment that promotes work-life balance, well-being, and open collaboration.

## Values in Action

The core values are the driving principles that guide the actions and decisions at Incubyte. These are the overarching ideas that shape the everything from day-to-day work to long-term plans.

- **Relentless Pursuit of Quality with Pragmatism** - Quality in the work that is delivered is the core identity of what is done at Incubyte. To always deliver high-quality work,
  to never compromise for short-terms gains over long-term value, the attention to detail, and the commitment to excellence are the hallmarks of the work done at Incubyte. This idealism is balanced with pragmatism, by ensuring that the work is delivered in a timely manner, and that the solutions are practical and feasible. Quality is not a one-and-done task, but an ever-evolving process. To translate this to more technical terms:
  - Practice Test-Driven Development (TDD)
  - Engage in Pair Programming
  - Maintain Robust CI/CD Pipelines
  - Refactor Code Regularly
  - Conduct Thorough Code Reviews
  - Implement Automated Testing Strategies
  - Follow Industry Best Practices
- **Extreme Ownership** - To take extremem ownership means to take full responsibility for the work that is done, the decisions to it, and the outcomes out of it. There is no running away for mistakes, and no blaming other for failures. Whether it the wins or the losses, the mantle is ours to carry. This demands a pro-active and initiave-driven approach to work. This encompasses things from picking up work without waiting to be assigned to following the boy scout rule even in places where no one sees. To be congizant of one's work and its impact on the larger picture. To ensure that the efforts lead to a collective success, and not just individual accomplishments.
- **Proactive Collaboration** - In a remote first environment like Incubyte, collaboration is not just a box to tick, but a team sport that is played everyday. It is about pooling the collective knowledge, skills, and talents of the team to achieve the shared goals. It is as much about helping out and as it is about asking for help, and being an efficient group, rather than efficients members. It becomes critically important in a remote setup to make sure that we work in tandem and are never out of sync.
- **Active Pursuit of Mastery** - The relentless pursuit of quality cannot be materialized without an attitude to continuosly learn and grow. The emphasis on improving one's skillset and capabilities is also a fundamental part of the culture here. And again it is not about just individual growth, but also about growing together. This is about always being curious, trying to learn new things, whether it is a tool, a framework, a design pattern, or a new way of thinking. Personal learning, sharing the knowledge, building things out of the love of the game, and mentoring others are all part of this value.
- **Give, Invite, and Act on Feedback** - To grow and to grow together, feedback is a critical part of the process. It is about giving feedback in a constructive and actionable manner, inviting feedback from others, and acting on it to improve. This is about creating a culture where feedback is not feared or avoided, but embraced as a tool for growth and improvement. It is about being open to receiving feedback, and being willing to act on it to make things better.
- **Create Ecstatic Customers** - None of the values matter if the end result is not a happy customer. Everything that is done is to bring the visions and ideas to fruition. As stated in the playbook, we are in the "business of building dreams". We are not just vendors, services provides, or contractors, but we are trusted partners and allies in the journey of our customers. The end goal is to create ecstatic customers, who are not just satisfied, but delighted with the work that is done. This is about going above and beyond to exceed expectations, and to create a lasting impact on the customers' lives and businesses.

## Reflection on Values

The values of Incubyte are what made me gravitate towards it. Every single value was something I practiced or wanted to practice. I sincerely believed those values were not just words on a page, but principles that could guide my actions and decisions. I wanted to be part of a team that shared these values and worked towards a common goal.

### Challenge - "Give, Invite, and Act on Feedback"

Although, I followed a lot of the values, without materializing them into words, "Give, Invite, and Act on Feedback" is something that has been a bit absent in my career. Perhaps, the culture was not there, or perhaps, I was not very well equipped to give to take feedback, or even realized the importance of it. So, preaching and practicing this value would be something new and a challenge that I would want to take on. I would like to be more open to receiving feedback, and also be more proactive in giving feedback to others.
