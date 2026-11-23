## 2026-11-03 21:15:58:<br>Category: Development Documentation<br>Topic: Project Overview
Project ExpressiVector is a vector image creator designed to provide user precise control over the tools and mechanisms, targeting to be utilized to create high quality vector art, and accurate mathematical diagrams, while focusing on accessibility, maintainability and readability.
The project is written in python, backed by pygame (specifically, pygame-ce / pygame Community Edition). However, a remarkably amount of infrastructures are built from scratch, including the vector composing geometry math and the UI widget system.
The project was targeted to finish major development in 2 weeks, but future maintainance are expected.
Specific schedule is the following:
- Week 1 Weekdays: Widget System
- Week 1 Weekend:  Vector Image composition
- Week 2 Weekdays: Utility, integration and features
- Week 2 Weekend:  Cleanup, doc, aesthetic

## 2026-11-03 21:44:17:<br>Category: Personal Journal<br>Topic: Project Overview
Yes, a break from physics engine, but into the exact same field of mathematics that is never the less simplier: Vector Images.
Specifically, the project for this week, as well as next week is: ExpressiVector, "a vector image creator capable of producing high quality *(depends on the artist)* vector art, and *(hopefully)* precise mathematical diagrams".
*Unlike the physics engine, this one for me is completely out in the fields. I have no experience with both the topic and the environment / language, and all I have is my generic programming and mathematical knowledge, as well as ambitions. Lots of ambitions.*
*However, lack of knowledge does led to lack of confidence, as I am researching desperately for how to batch draw triangles in pygame.*
This project is indeed abrupt and unusual as I am not using C++. That's because this is a school project.
But what makes it different is that 90% of the things are beyond whatever my teacher was expecting. I was designing this project to be a serious, production level software product instead merely an *assignment*.
That said, I believe this project could qualify for being an exception of the "No school project" restriction of Hackclub. If not, then I'll just remove the 10% features demanded by my teacher, submit that 10% to school and the rest of 90% for Terra, in which now they are separate projects.
On that note, just like stated earlier, the development in python is pretty unfamiliar to me as I am still learning the syntax and langauge intrinsics, therefore the development efficiency is expected to be quite pathetic for the first few days.
*And it cannot be over stated about how much I HATE Python. It is the most redundent, convoluted and inefficient language ever. It is, in my regard, the worse way to create any sort of application.*
*Remember the project overview above? Remember I listed "accessibility, maintainability, readability" and all that? Guess why me, the system programmer that values performance and execution efficiency over everything, didn't put "performance" up there? That's because I've lost all my hopes in python to be anywhere from optimised. The language is inherently flawed in aspect of being any efficient.*

## 2026-11-08 21:09:07:<br>Category: Development Report<br>Topic: Infrastructure Development Retrospective
As the completion of the first viable tool: Stroke was accomplished, the first week of development was marked finished.
The focus of this week was mostly infrastructure and basic environments. However, despite the lack of experience and the lack of infrastructure, the progress on the project was surprisingly substancial.
During this week, the general UI Widget System was implemented. Now all UI can be built on top of the existing architecture without repeating implementation.
The Core Engine and Canvas Management of the project was also implemented.
Other additional progress include the preliminary interface, the theme inspired by Photoshop, and the extra specialized UI widgets implemented for future usage.

## 2026-11-16 23:36:24:<br>Category: Development Report<br>Topic: Week 2 Development Retrospective
In this week, massive enhancement of the UI system infrastructure, and confirmation of the application UI system was achieved.
The UI system was heavily refactored, and numerous new widgets are added.
Simultaneously, the main UI design of the application was settled, and mostly implemented.
Unfortunately, however, the development couldn't finish in the planned 2 weeks, therefore one more week must be dedicated to the development of this project.

## 2026-11-22 21:08:53:<br>Category: Personal Journal<br>Topic: Final Completeion of The Project
First of all, despite all factors, this project was quite a failure in the same perspective of my usual judgement.
After the first week where the infrastructure were built, all seriousness I had regarding this project were gone.
Especially when I realized the nature of Python, I utterly gave up on my original ambitious goal of a maintainable, expandable UI system infrastructure, and a mathematically elegant vector image engine. The computational power Python offer is just inherently insufficient for such target. In a serious production to make a project with Python, any heavy lifting logic must be implemented in C/C++ or any other low level language and expose API to Python. In my opinion, the way I approached the problem in this project where I implement all infrastructures from scratch, *like how I did it in C++*, is fundamentally flawed in Python, simply because how inefficient the language itself is.
However, the credit of the failure cannot all be blamed on Python. Since this was my first time building a general UI library, I've made several flawed decisions, in which severely affected the expandability of the infrastructure. And my manner of "it is inefficient as is, just ship it" regarding the project contributes to the result a lot as well.
*And yes, excerpting a famous quote here: "We've spaghettied our way to final completion."*

**Lost resources due to slow review**
week 3: 14 water, 6 bok choy seeds and 8 cabbage seeds
week 4: 21 water, 10 banana, 15 eggplant