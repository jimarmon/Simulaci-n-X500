# Escenario de IMAV2026- Dron X500 (Visión)

Simulación de un dron X500 (con física ajustada a 2.3 kg) operando en un escenario de concurso mediante Optical Flow y evasión sin GPS en PX4/Gazebo.

## Instalación

Copia los archivos de este repositorio a tu instalación de PX4:
```bash
cp -r worlds/* ~/PX4-Autopilot/Tools/simulation/gz/worlds/
cp -r models/* ~/PX4-Autopilot/Tools/simulation/gz/models/

## Ejecución
Coordenadas pra ser lanzaado en la pista derecha

cd ~/PX4-Autopilot
export PX4_GZ_WORLD=escenario_concurso
export PX4_GZ_MODEL_POSE="5.75,1.0,0.2,0,0,0"
make px4_sitl gz_x500_vision

## Configuración (Vuelo sin GPS)

param set EKF2_GPS_CTRL 0
param set EKF2_OF_CTRL 1
param set EKF2_RNG_CTRL 1
param set SYS_HAS_GPS 0
param save
reboot

Si quieren usar el gps de debe de desaactivr el opticalflow
