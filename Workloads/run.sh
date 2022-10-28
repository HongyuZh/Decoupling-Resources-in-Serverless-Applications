cd chameleon
docker build -t chameleon:v1 .
cd ../

cd linpack
docker build -t linpack:v1 .
cd ../

cd matmul
docker build -t matmul:v1 .
cd ../

cd float_operation
docker build -t float_operation:v1 .
cd ../

cd pyaes
docker build -t pyaes:v1 .
cd ../