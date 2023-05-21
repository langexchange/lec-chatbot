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