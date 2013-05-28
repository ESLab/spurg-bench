Spurg-Bench
----------------------------------------

Spurg-Bench is a Q&D microbenchmark software, made because of need of
specific, easily customizable loads for testing behavior of
schedulers. For a more detailed description of the software please
consult docs/spurg-bench.pdf

  Usage
----------------------------------------

Build the operations using
./build_backend.py

Run simple run:
cd runners; ./simple_run.py -o 100000 -n 4 -l 0.5

Customizing and using all included features requires reading the code
and the documentation.
