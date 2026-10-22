import asyncio
import sys
import termios
import tty
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed, OffboardError

# Variables globales de velocidad
vx, vy, vz = 0.0, 0.0, 0.0

async def enviar_comandos_offboard(drone):
    """
    Bucle crítico de 20Hz (cada 0.05s). 
    PX4 exige recibir comandos de velocidad constantemente para no activar el failsafe de Offboard.
    """
    global vx, vy, vz
    while True:
        try:
            await drone.offboard.set_velocity_body(VelocityBodyYawspeed(vx, vy, vz, 0.0))
        except Exception:
            pass
        await asyncio.sleep(0.05)

async def run():
    global vx, vy, vz
    drone = System()
    
    print("Conectando al dron en el simulador...")
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("¡Conexión establecida con éxito!")
            break

    print("Inyectando parámetros para vuelo autónomo por Odometría Visual (VIO) sin GPS...")
    # 1. Configuración de navegación por visión (x500_vision)
    await drone.param.set_param_int("SYS_HAS_GPS", 0)
    await drone.param.set_param_int("EKF2_GPS_CTRL", 0)
    await drone.param.set_param_int("EKF2_OF_CTRL", 0)
    await drone.param.set_param_int("EKF2_RNG_CTRL", 0)
    await drone.param.set_param_int("EKF2_EV_CTRL", 15)
    await drone.param.set_param_int("EKF2_HGT_REF", 3)
    
    # 2. Bypass de seguros físicos y pre-armado
    await drone.param.set_param_int("COM_PREARM_MODE", 0)
    await drone.param.set_param_int("COM_ARM_WO_GPS", 1)
    await drone.param.set_param_int("SYS_HAS_MAG", 0)
    
    # 3. Bypass de pérdida de enlace y estación terrena
    await drone.param.set_param_int("NAV_RCL_ACT", 0)
    await drone.param.set_param_int("NAV_DLL_ACT", 0)
    await drone.param.set_param_int("COM_RC_IN_MODE", 4)
    await drone.param.set_param_int("COM_LOW_PWR_ACT", 0)

    print("Esperando 7 segundos a que la IMU y el estimador EKF2 alcancen estabilidad...")
    await asyncio.sleep(7)

    print("Iniciando flujo previo de Offboard...")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print(f"Aviso de inicio offboard: {e}")

    # Lanzamos el emisor de comandos en segundo plano de forma permanente
    asyncio.create_task(enviar_comandos_offboard(drone))
    await asyncio.sleep(1)

    print("Armando motores...")
    await drone.action.arm()

    print("¡Despegando y estabilizando altura (2.3 kg en curso)...!")
    vz = -2.0  # Impulso inicial hacia arriba
    await asyncio.sleep(2.0)
    vz = 0.0   # Se queda flotando quieto

    print("\n" + "="*33)
    print("🚁 CONTROLES POR TECLADO ACTIVADOS")
    print("="*33)
    print(" W / S : Adelante / Atrás")
    print(" A / D : Izquierda / Derecha")
    print(" Q / E : Subir / Bajar")
    print(" X     : FRENAR (Mantenerse flotando)")
    print(" C     : Aterrizar y Salir")
    print("="*33 + "\n")
    
    loop = asyncio.get_running_loop()
    speed = 2.5 # Velocidad en m/s

    # Bucle seguro de lectura de teclado no bloqueante
    while True:
        key = await loop.run_in_executor(None, sys.stdin.read, 1)
        
        if key == 'w': vx, vy, vz = speed, 0.0, 0.0
        elif key == 's': vx, vy, vz = -speed, 0.0, 0.0
        elif key == 'a': vx, vy, vz = 0.0, -speed, 0.0
        elif key == 'd': vx, vy, vz = 0.0, speed, 0.0
        elif key == 'q': vx, vy, vz = 0.0, 0.0, -speed
        elif key == 'e': vx, vy, vz = 0.0, 0.0, speed
        elif key == 'x': vx, vy, vz = 0.0, 0.0, 0.0
        elif key == 'c': 
            break

    print("\nAterrizando con seguridad...")
    vx, vy, vz = 0.0, 0.0, 0.0
    await drone.offboard.stop()
    await drone.action.land()

if __name__ == "__main__":
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
