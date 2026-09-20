# Gemini Enterprise + BigQuery Conversational Analytics

Bare-bones walkthrough of publishing a BigQuery Conversational Analytics agent and using it from Gemini Enterprise.

Source: [Conversational analytics in BigQuery](https://docs.cloud.google.com/bigquery/docs/conversational-analytics)

Enable the Gemini in BigQuery and Gemini for Google Cloud APIs for the project.

![Enable Gemini in Data Analytics APIs](assets/Screenshot%202026-09-20%20at%209.50.48%20am.png)

Select the BigQuery tables and views the agent can query.

![Select BigQuery sources](assets/Screenshot%202026-09-20%20at%2010.35.32%20am%20redacted.png)

Save the agent in Conversational Analytics Studio and try a preview question.

![Agent editor and preview](assets/Screenshot%202026-09-20%20at%2010.37.52%20am%20redacted.png)

Choose publish channels, including Agent Registry so Gemini Enterprise can import it.

![Publishing channels](assets/Screenshot%202026-09-20%20at%2011.23.09%20am.png)

Confirm the agent is published to BigQuery, Conversational Analytics API, Data Studio, and Agent Registry.

![Published successfully](assets/Screenshot%202026-09-20%20at%2011.23.32%20am.png)

The publish dialog then shows the agent as registered in Agent Registry.

![Registered in Agent Registry](assets/Screenshot%202026-09-20%20at%2011.26.32%20am.png)

Open the registered agent in Agent Platform Registry to inspect its card and ADK snippet.

![Agent Registry overview](assets/Screenshot%202026-09-20%20at%2011.29.44%20am%20redacted.png)

Import the agent into a Gemini Enterprise app from Agent Registry.

![Import agent into Gemini Enterprise](assets/Screenshot%202026-09-20%20at%2011.46.54%20am%20redacted.png)

The agent appears under From your organization in the Gemini Enterprise Agents picker.

![Gemini Enterprise agents](assets/Screenshot%202026-09-20%20at%2011.47.32%20am.png)

The first chat can prompt for extra authorization before queries run.

![Additional authorization](assets/Screenshot%202026-09-20%20at%2011.48.50%20am.png)

After auth, the agent retrieves table context, runs SQL, and answers.

![Query with retrieved context](assets/Screenshot%202026-09-20%20at%2011.49.29%20am%20redacted.png)

Follow-up questions can return structured result tables from the same dataset.

![Tool-call result table](assets/Screenshot%202026-09-20%20at%2011.50.38%20am.png)

Gemini Enterprise can collect thumbs-up feedback on the answer.

![Feedback on the answer](assets/Screenshot%202026-09-20%20at%2011.50.55%20am.png)

Later turns can keep using the same agent for other breakdowns of the data.

![Follow-up analysis](assets/Screenshot%202026-09-20%20at%2012.18.19%20pm.png)
