# Instalalación 
Para estos pasos, se deberá clonar el repositorio del cloud-slicemanager como usuario **root**.

Podrá seguir los siguientes pasos para la descarga:

```bash {"id":"01HWB4H0QJW56YEFS5WA2VDN5V"}
sudo -i
git clone https://github.com/noaJ4Q/cloud-slice-manager.git
cd cloud-slice-manager
```
Una vez que se encuentre en la ruta del directorio creado, podrá continuar con los próximos pasos.

# Pasos para arranque
Deberá ejecutar el script `init.sh`, el cual instalará las librerias necesarias para el proyecto y creará un servidor flask:
```bash {"id":"01HWB4H0QJW56YEFS5WD3HDZ16"}
bash init.sh
```
Finalmente
```sh {"id":"01HZ7JWHHSBR26VZF89J5S2R1W"}
sliceManager
```