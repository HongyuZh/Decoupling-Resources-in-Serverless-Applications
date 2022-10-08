cd Workloads

cd chameleon
docker build -t chameleon:v1 .
cd ../

cd linpack
docker build -t linpack:v1 .
cd ../

cd matmul
docker build -t matmul:v1 .
cd ../
