## Step 1: Installation of the LISFLOOD model

There are several ways to get lisflood model and to run it on your machines: 

1. Using the Docker image `jrce1/lisflood`
2. Using pip tool together with conda to easily install dependencies
3. Obtaining the source code, by cloning repository or downloading source distribution, and install dependencies.

The suggested way is using the official Docker image, since it's not trivial to install PCRaster and GDAL for average users.

In this page all different options are described. Feel free to pick up what suits you best.

 
### A) Docker image (suggested)


You can use the updated docker image to run lisflood, so without taking care to install dependencies on your system.
First, you pull image from repository.

```bash
docker pull jrce1/lisflood
```

Copy Test catchment files from container to your host, using mapped volumes. `usecases` is the folder in docker where test catchments are.

```bash
docker run -v /absolute_path/to/my/local/folder:/usecases jrce1/lisflood:latest usecases
```

After this command, you can find all files to run tests against a catchment under the directory you mapped: `/absolute_path/to/my/local/folder/`,

```bash
/absolute_path/to/my/local/folder/LF_ETRS89_UseCase
/absolute_path/to/my/local/folder/LF_lat_lon_UseCase
```

where `LF_ETRS89_UseCase` and `LF_lat_lon_UseCase` are folders containing test data.

Now, you can run LISFLOOD as a docker container to test the catchment. Only thing you need to do is to map a test folder to the container folder `input`, by using Docker `-v` option. 
In the XML settings file, all paths are adjusted to be relative to the very same settings file, so you don't need to edit paths, as long as you keep same folder's structure.


Execute the following docker command to run the simulation:

```bash
docker run -v /absolute_path/to/my/local/folder/LF_ETRS89_UseCase:/input jrce1/lisflood /input/settings/cold.xml
```

Once LISFLOOD finished, you can find reported maps in `/absolute_path/to/my/local/folder/LF_ETRS89_UseCase/out/` folder.


### B) Pypi packaged LISFLOOD and conda env

Using conda environment is very handy since installing latest PCRaster and its dependencies is pretty straightforward.

1. Install [miniconda](https://docs.conda.io/en/latest/miniconda.html) 
2. Create a conda env named "lisflood" and install dependencies:
```
conda create --name lisflood python=3.7 -c conda-forge
conda activate lisflood
conda install -c conda-forge pcraster
pip install lisflood-model
```

Command above will also install the executable `lisflood` in the conda env, so that you can run LISFLOOD with the following:
```bash
lisflood /absolute_path/to/my/local/folder/<TestCatchmentFolder>/settings/cold_day_base.xml
```

*Note:* You can use a straight python virtualenvironment to install lisflood-model package but then you have to setup PCRaster/GDAL/NetCDF libraries.

### C) Using the python source code

You can download code and dataset for testing the model (or to contribute with bug fixes or new features).
Follow this instruction for a basic test (some sample catchments are included in this repository under
[tests/data](https://github.com/ec-jrc/lisflood-code/tree/master/tests/data) folder)

1. **Clone the master branch of this repository (you need to have git installed on your machine).**

    ```bash
    git clone --single-branch --branch master https://github.com/ec-jrc/lisflood-code.git
    ```

2. **Install requirements into a python 3 conda env**

```bash
conda create --name lisflood python=3.7 -c conda-forge
conda activate lisflood
conda install -c conda-forge pcraster
cd lisflood-code
pip install -r requirements.txt
```

If you don't use conda but a plain virtualenv, you need to install PCRaster and GDAL by your own and include its python interface in PYTHONPATH environment variable.
For details, please follow instruction on [official docs](https://pcraster.geo.uu.nl/pcraster/4.3.1/documentation/pcraster_project/install.html).
    

3. **Run a cold run for the test catchment**

    Now that your environment should be set up to run lisflood, you may try with a prepared settings file for test catchment included into the tests/data folder:
    
    ```bash
    python src/lisf1.py tests/data/<TestCatchmentFolder>/settings/cold.xml
    ```
4. **Run LISFLOOD unit tests**

    ```bash
    pytest tests/
    ```
    You may need to install ```pytest```, ```pytest-cov```, ```pytest-mock``` and ```gdal``` packages before running the tests, using the command ```pip install <package name>``` for each one.
  
If commands above succeeded without errors, producing dis.nc into `tests/data/<TestCatchmentFolder>/outputs` folder, your lisflood installation was correct.
