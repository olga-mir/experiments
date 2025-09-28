from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "meta-llama/Llama-2-7b-chat-hf"
api_token = ""
model_dir = "./llama-2-7b-chat-hf"

# Load tokenizer and model using the API token
tokenizer = AutoTokenizer.from_pretrained(model_name, token=api_token)
model = AutoModelForCausalLM.from_pretrained(model_name, token=api_token)

# Optionally, save the model and tokenizer locally if needed
tokenizer.save_pretrained(model_dir)
model.save_pretrained(model_dir)



# # Assuming 'model' is already loaded with float32 precision
# model.half()  # Convert model to float16
# # Save the model in float16
# model.save_pretrained(model_dir)
# model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, use_auth_token=api_token)

