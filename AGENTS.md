# Overview

This repo is a collection of small usually stand-alone experiments.

Each folder name follows format `NN-YYYY.MM-SLUG` where
NN - number from 00 to 99, it is used to show the latest experiements at the top of the folder. Some numbers can be missing, some can be duplicated which is ok.
YYYY.MM - year and month
SLUG - short slug describing the experiment.

In some cases experiments can be combined together but still be a first class citizen. In this case they will share the number and the date, but have different slug

# Guidlelines

* For python always use `uv`
* If experiment has a handful operations to deploy, run and explore the idea then create Taskfile to automate these tasks.
* For projects that need to be deployed GCP use environment variables for project numbers and other sensitive information. Don't commit them to the code.
* For any env var used add to a special 'preflight' task that fails on required vars missing and warns on optionals
