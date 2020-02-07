import iris
import os
import xarray as xr
import numpy as np

def file_to_cube(filename, filepath, constraints={}):
    # Load a cube from a file
    cube = iris.load_cube(os.path.join(filepath, filename), iris.AttributeConstraint(**constraints))
    print(f'Cube loaded from {filename}')
    return cube

def file_to_cubelist(filename, filepath, constraints={}):
    # Load a cube from a file
    cubelist = iris.load(os.path.join(filepath, filename), iris.AttributeConstraint(**constraints))
    print(f'Cubelist loaded from {filename}')
    return cubelist
    
def cube_to_da(cube):
    # Convert Iris cube to Xarray DataArray
    return xr.DataArray.from_iris(cube)

def cube_to_ds(cube):
    # Convert Iris cube to Xarray Dataset
    return xr.DataArray.from_iris(cube).to_dataset()
    
def ds_to_zarr(dataset, zarr_store, chunks={'time':10, 'grid_latitude':219, 'grid_longitude':286}, append_dim='time', **kwargs):
    # Write dataset to new zarr store
    # OR append dataset to an existing zarr store
    dataset = dataset.chunk(chunks=chunks)
    if os.path.isdir(zarr_store):
        dataset.to_zarr(zarr_store, consolidated=True, append_dim=append_dim, **kwargs)
        print(f'Appended dataset to {zarr_store}')
    else:
        dataset.to_zarr(zarr_store, mode='w', consolidated=True, **kwargs)
        print(f'Written dataset to {zarr_store}')

def datetimes_from_cube(cube):
    return xr.DataArray.from_iris(cube).time.data

def datetimes_from_zarr(zarr_store):
    return xr.open_zarr(zarr_store).time.data