# Gemini Enterprise + BigQuery Conversational Analytics

Bare-bones walkthrough of publishing a BigQuery Conversational Analytics agent and using it from Gemini Enterprise.

Source: [Conversational analytics in BigQuery](https://docs.cloud.google.com/bigquery/docs/conversational-analytics)

Enable the Gemini in BigQuery and Gemini for Google Cloud APIs for the project.

<img src="assets/step_01.png" width="450" alt="Enable Gemini in Data Analytics APIs">

Select the BigQuery tables and views the agent can query.

<img src="assets/step_02.png" width="700" alt="Select BigQuery sources">

Save the agent in Conversational Analytics Studio and try a preview question.

<img src="assets/step_03.png" width="700" alt="Agent editor and preview">

Choose publish channels, including Agent Registry so Gemini Enterprise can import it.

<img src="assets/step_04.png" width="450" alt="Publishing channels">

Confirm the agent is published to BigQuery, Conversational Analytics API, Data Studio, and Agent Registry.

<img src="assets/step_05.png" width="450" alt="Published successfully">

The publish dialog then shows the agent as registered in Agent Registry.

<img src="assets/step_06.png" width="450" alt="Registered in Agent Registry">

Open the registered agent in Agent Platform Registry to inspect its card and ADK snippet.

<img src="assets/step_07.png" width="700" alt="Agent Registry overview">

Import the agent into a Gemini Enterprise app from Agent Registry.

<img src="assets/step_08.png" width="700" alt="Import agent into Gemini Enterprise">

The agent appears under From your organization in the Gemini Enterprise Agents picker.

<img src="assets/step_09.png" width="700" alt="Gemini Enterprise agents">

The first chat can prompt for extra authorization before queries run.

<img src="assets/step_10.png" width="700" alt="Additional authorization">

After auth, the agent retrieves table context, runs SQL, and answers.

<img src="assets/step_11.png" width="700" alt="Query with retrieved context">

Follow-up questions can return structured result tables from the same dataset.

<img src="assets/step_12.png" width="700" alt="Tool-call result table">

Gemini Enterprise can collect thumbs-up feedback on the answer.

<img src="assets/step_13.png" width="450" alt="Feedback on the answer">

Later turns can keep using the same agent for other breakdowns of the data.

<img src="assets/step_14.png" width="700" alt="Follow-up analysis">
