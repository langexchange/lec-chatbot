# Langex chatbot for detecting pronunciation accuracy using STT model

## 1. Todos:
[ ] Understand how ctranslate can optimize inference process

## 2. Deploy:
Whisper dependencies
+ ffmpeg CLI
```console
sudo apt update && sudo apt install ffmpeg
```

+ OpenAI's tiktoken => Use Rust if tiktoken does not work.
+ ffmpeg-python 

## 2. Extension to xmpp msg
### 2.1. Message extension
```xml
<message>
	<body>
	</body>
	<langexbot xmlns="langex:chatbot">
		<feature-element>
	</langexbot>
</message>
```

1. Onboard
```xml
	<onboard xmlns="langex:chatbot:onboard"> </onboard>
```

2. Pronunciation Assessment
```xml
  <pronunc_assess xmlns="langex:chatbot:pronunc_assess"> </pronunc_assess>
```

## 3. Docker 
### 3.1. Build image
To effectively build the image by not reinstalling all packages whenever `requirements.txt` changed. You should execute `sudo make config-dockerd` to config `daemon.json` for docker daemon. Be careful that command will override all current configurations `daemon.json`. If it is in case, you should manually append configuration in `daemon.json` file in the current working directory to that system configuration `daemon.json` file.

### 3.2 Run container
Model is installed at `/root/.cache/huggingface` and `/usr/local/src/lec-chatbot/chatbot/models/whisper/model`. Please mount it to avoid downloading model whenever run the container.
```console
docker run -d --rm narutosimaha/lec-chatbot
```

## 4. Deployment backlog
[ ] Set up certificate for file service.