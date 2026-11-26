# What works best, by capability (r6.4)

Each row is one kind of job this machine was tested on, with the setup in production today and the best alternative found. Click a capability for why, what else was tried, and the experiments behind it, best results first. A setup is a model running on an engine (the software that runs it) with a setting; engines have [their own page](engines.md).

| Capability | What it means | In production | Best alternative |
|---|---|---|---|
| [Text and reasoning](text.md) | Answering questions, summarising and pulling facts from documents, everyday writing. | Qwen3.8-Flash-Next on Halogen | Qwen3.8-27B on Talus |
| [Office tools](tool-use.md) | Calling office tools: create a document, send an email, look up a client. | Qwen3.8-Flash-Next on Halogen | - |
| [Speech to text](speech-to-text.md) | Turning recordings into text. | Whisper large-v3-turbo on whisper.cpp | - |
| [Who said what](speaker-labelling.md) | Tagging each line of a transcript with who said it. | WeSpeaker + Silero, one enrolled speaker on WeSpeaker + Silero | - |
| [Memory](memory.md) | Keeping an assistant's notes about a person up to date without inventing or keeping rejected facts. | Qwen3.8-Flash-Next on Halogen | Inkling-2-Mini on llama.cpp |
| [Voice output](voice-output.md) | Reading text aloud in a natural voice (narration). | Chatterbox, voice cloned from VCTK speaker p239 on Chatterbox | Kokoro bf_emma on Kokoro |
| [Images](images.md) | Generating and editing pictures from a description. | FLUX.1-schnell (Q4_0) on stable-diffusion.cpp | Qwen-Image-2.1 on diffusers on ROCm PyTorch |
| [Music](music.md) | Generating songs with sung lyrics. | nothing yet | ACE-Step 1.5 Turbo on audio.cpp |
| [Vision](vision.md) | Understanding images and scanned pages. | not yet tested | - |
| [Fine-tuning](fine-tuning.md) | Training a model on the box on your own examples. | nothing yet | - |
| [Coding agents](coding-agent.md) | Fixing and changing real software on its own, checked by each project's tests. | Qwen3.8-Flash-Next on Halogen | Qwen3.8-27B on Talus, Ornith 1.5 35B on llama.cpp |

Engines: production runs on **Halogen**; the fallback is **HTR on vLLM** ([engines](engines.md)).
