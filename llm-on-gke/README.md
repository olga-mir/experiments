# LLM on GKE





# References

* Google Blog blogpost [Gemma on Google Kubernetes Engine deep dive: New innovations to serve open generative AI models](https://cloud.google.com/blog/products/containers-kubernetes/serving-gemma-on-google-kubernetes-engine-deep-dive), April 11, 2024
  * Serving stacks diagram to help understand different components and their relationships

* [Google official tutorials deploying Gemma on GKE](https://cloud.google.com/kubernetes-engine/docs/tutorials/serve-gemma-gpu-vllm)
  * The blog post linked above gives a quick introduction to each stack. This tutorial colleciton walks through deploying each one of them, explore the doc tree on the left.
  * TPUs
    * Newly announced JetStream inference engine
  * GPUs
    * vLLM: OSS LLM serving framework. ([vllm repo](https://github.com/vllm-project/vllm)))
    * TGI - Text Generation Inference: OSS LLM serving framework from Hugging Face.
    * TensorRT-LLM.

* https://github.com/GoogleCloudPlatform/kubernetes-engine-samples/tree/main/ai-ml

