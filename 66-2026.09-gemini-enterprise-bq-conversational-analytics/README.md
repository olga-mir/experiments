# Gemini Enterprise + BigQuery Conversational Analytics

Walkthrough of creating and publishing a BigQuery Conversational Analytics agent and using it from [Gemini Enterprise app](https://cloud.google.com/blog/products/ai-machine-learning/whats-new-in-gemini-enterprise)

Source: [Conversational analytics in BigQuery](https://docs.cloud.google.com/bigquery/docs/conversational-analytics)

This walkthrough is driven fully through console. What is and isn't supported in IaC or REST APIs was not verified.


## APIs

Enable the Gemini in BigQuery and Gemini for Google Cloud APIs for the project.

<img src="assets/step_01.png" width="450" alt="Enable Gemini in Data Analytics APIs">
</br>
</br>
</br>

## Datasources

Select the BigQuery tables and views the agent can query. There is an option to add pre-defined verifier queries

<img src="assets/step_02.png" width="700" alt="Select BigQuery sources">
</br>
</br>
</br>

## Preview and publish

Save the agent in Conversational Analytics Studio and try a preview question.

<img src="assets/step_03.png" width="700" alt="Agent editor and preview">
</br>
</br>
</br>

Choose publish channels, including Agent Registry so Gemini Enterprise can import it.

<img src="assets/step_04.png" width="450" alt="Publishing channels">
</br>
</br>
</br>

Confirm the agent is published to BigQuery, Conversational Analytics API, Data Studio, and Agent Registry.

</br>
<img src="assets/step_05.png" width="450" alt="Published successfully">
</br>
</br>
</br>

# Integrate with Gemini Enterprise Agent Platform

The publish dialog then shows the agent as registered in Agent Registry.

</br>
<img src="assets/step_06.png" width="450" alt="Registered in Agent Registry">
</br>
</br>
</br>

Now this agent can be used by other agents, as any other compatible agent in Agent Registry

<img src="assets/step_07.png" width="700" alt="Agent Registry overview">
</br>
</br>
</br>

Import the agent into a Gemini Enterprise app from Agent Registry. This requires the Agent Card json that is available in the Data Agent interface.

<img src="assets/step_08.png" width="700" alt="Import agent into Gemini Enterprise">
</br>
</br>
</br>

The agent appears under From your organization in the Gemini Enterprise Agents picker.
</br>
</br>
<img src="assets/step_09.png" width="700" alt="Gemini Enterprise agents">
</br>
</br>
</br>

# Interact with Agent in Gemini Enterprise

The first chat can prompt for extra authorization before queries run. "Authorize" will open OAuth pop-up button which will then allow agent to act on my behalf, using permissions that are scoped to my user.

<img src="assets/step_10.png" width="700" alt="Additional authorization">
</br>
</br>
</br>

After auth, the agent retrieves table context, runs SQL, and answers.

<img src="assets/step_11.png" width="700" alt="Query with retrieved context">
</br>
</br>
</br>

Follow-up questions can return structured result tables from the same dataset. Tool calls should not be part of the same table - it is operational data that belongs to team who owns the agent, not the users, but this is artifact of the project itself, not relevant to this demo

</br>
<img src="assets/step_12.png" width="700" alt="Tool-call result table">
</br>
</br>
</br>

Gemini Enterprise can collect thumbs-up feedback on the answer.

</br>
<img src="assets/step_13.png" width="450" alt="Feedback on the answer">
</br>
</br>
</br>

Later turns can keep using the same agent for other breakdowns of the data.

</br>
<img src="assets/step_14.png" width="700" alt="Follow-up analysis">
</br>
</br>
</br>
