# Vishing Challenge

As the name suggests, this is a vishing challenge Python script. The original idea was taken from [JMFD](https://x.com/hackandbackpack) and his project [phoneybaloney](https://github.com/hackandbackpack/phoneybaloney). He presented this cool challenge at KernelCon 2024, and my friends and I thought it was a great idea. So, we decided to port this excellent project to a Spanish version with some additional infrastructure modifications.

We presented this challenge at BSides CDMX 2024 as part of the new Social Engineering Village.

For any questions or comments, you can reach us on X [@elbrujo](https://x.com/todmephis) and [@darkit](https://x.com/dark1t).

## Installation

We recommend using this script in a virtual environment.

```bash
# If you're running on macOS:
brew install portaudio
# If you're running on GNU/Linux - Ubuntu/Debian (Not tested yet):
sudo apt-get install portaudio19-dev python-all-dev
git clone https://github.com/todmephis/Vishing-Challenge.git
cd Vishing-Challenge
python3 -m venv v-chall
source v-chall/bin/activate.fish # I'm a fish user, adapt this for bash
pip install -r requirements.txt
```

The Python version this was tested on: `Python 3.12.4`

## Usage

Within your virtual environment, just run `python3 vishing-challenge.py`. You will need a microphone to interact with phoneybaloney, as it only allows for input via voice. After launching the script, you are ready to talk your way through the designed scenarios.

## The Challenge - El Reto

La empresa Arnet te ha contratado para realizar ataques de ingeniería social a sus sistemas. Comenzarás con una llamada telefónica al conmutador automático (este es el primer escenario).

Mediante la terminal, te conectarás a varios escenarios que simularán ser empleados de Arnet, con quienes tendrás que hablar e interactuar para resolver este reto. Cada conversación, cada interacción, será una pieza clave en el rompecabezas que tendrás que resolver.

Tendrás que recabar información y pistas que te ayudarán a obtener algo muy secreto que no debería compartirse por teléfono (la bandera).

### Nota:

Para cambiar de extensión solo di "Llamar extensión <Numero>"

Para terminar la llamada solo di "Terminar llamada"

## Note

We use some AWS resources that might be down when you want to use this script. If that happens, just [ping me on X](https://x.com/todmephis), and I will deploy the environment in our backend for you :)

---

Once again, thank you [JMFD](https://x.com/hackandbackpack) for this cool script.
