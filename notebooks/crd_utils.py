import iris
import os
import copy
import xarray as xr
import numpy as np

import umdates_utils as um

## FILES -> IRIS
def file_to_cube(filename, filepath, constraints={}, verbose=True):
    # Load a cube from a file
    cube = iris.load_cube(os.path.join(filepath, filename), iris.AttributeConstraint(**constraints))
    if verbose: print(f'Cube loaded from {filename}')
    return cube

def file_to_cubelist(filename, filepath, constraints={}, verbose=True):
    # Load a cube from a file
    cubelist = iris.load(os.path.join(filepath, filename), iris.AttributeConstraint(**constraints))
    if verbose: print(f'Cubelist loaded from {filename}')
    return cubelist


## IRIS -> XARRAY
def cube_to_da(cube):
    # Convert Iris cube to Xarray DataArray
    return xr.DataArray.from_iris(cube)

def cube_to_ds(cube):
    # Convert Iris cube to Xarray Dataset
    return xr.DataArray.from_iris(cube).to_dataset()

def cubelist_to_dalist(cubelist):
    # Convert Iris Cubelist to list of Xarray DataArrays
    dalist = []
    for cube in cubelist:
        dalist.append(cube_to_da(cube))
    return dalist

def cubelist_to_dataset(cubelist):
    # Convert Iris cubelist to Xarray Dataset
    dalist = cubelist_to_dalist(cubelist)
    return xr.merge(dalist)


## XARRAY + IRIS -> ZARR
def ds_to_zarr(dataset, zarr_store, chunks=None, append_dim='time', verbose=False, **kwargs):
    # Write dataset to new zarr store
    # OR append dataset to an existing zarr store
    if chunks:
        dataset = dataset.chunk(chunks=chunks)
    if os.path.isdir(zarr_store):
        dataset.to_zarr(zarr_store, consolidated=True, append_dim=append_dim, **kwargs)
        if verbose: print(f'Appended dataset to {zarr_store}')
    else:
        dataset.to_zarr(zarr_store, mode='w', consolidated=True, **kwargs)
        if verbose: print(f'Written dataset to {zarr_store}')

def cubelist_to_zarr(cubelist, cubenames=None, coordname_mapping=None, **kwargs):
    # Write cubelist to new zarr store
    # OR append cubelist to an existing zarr store
    if cubenames or coordname_mapping:
        rename_cubes(cubelist, cubenames, coordname_mapping, dryrun=False, verbose=False)
    
    dataset = cubelist_to_dataset(cubelist)
    ds_to_zarr(dataset, **kwargs)

    
## TIMES FROM DATA
def datetimes_from_cube(cube):
    return xr.DataArray.from_iris(cube).time.data

def datetimes_from_zarr(zarr_store):
    return xr.open_zarr(zarr_store).time.data


## IRIS CUBE_NAME + COORD_NAME TOOLS
def unique_coords_list(cubelist):
    unique = []
    for cube in cubelist:
        for coord in cube.coords():
            if not coord in unique:
                unique.append(coord)
    return copy.deepcopy(unique)

def get_new_coord_names(coords, verbose=False):
    names = []
    renamed = []
    for coord in coords:
        name = coord.name()
        names.append(name)
        n = names.count(name)
        if n > 1:
            new_name = f'{name}_{n-1}'
            renamed.append((coord, new_name))
        if verbose:
            print(f'Names: {names}')
    if verbose:
        print(f'Names: {names}')
    return tuple(zip(*renamed))

def get_new_cubename(cube):
    suffixes = [cube.standard_name or str(cube.attributes['STASH'])]  
    # [cube.name()] leads to repeated cell_method suffixes for anonymous cubes
    coord_names = [coord.name() for coord in cube.coords()]
    
    if 'pressure' in coord_names:
        suffixes.append('at_pressure')
    
    if 'height' in coord_names:
        heights = cube.coord('height')
        if len(heights.points) > 1:
            suffixes.append('at_height')
        else:
            height = str(int(heights.points[0].round()))
            units = str(heights.units)
            suffixes.append(f'at_{height}{units}')
    
    for cell_method in cube.cell_methods:
        method = cell_method.method.replace('imum', '')
        suffixes.append(method)
    
    return '_'.join(suffixes)

def rename_cubes(cubelist, cubenames=None, new_coordnames=None, dryrun=False, verbose=True):
    # Rename cubes and coordinates in place where necessary
    
    if cubenames==None:
        cubenames = [cube.name() for cube in cubelist]
        
    if new_coordnames==None:
        new_coordnames = get_new_coord_names(unique_coords_list(cubelist))
    
    for cube in cubelist:
        # Rename cube if duplicate or unknown
        if cube.standard_name == None or cubenames.count(cube.name()) > 1:
            new_name = get_new_cubename(cube)
            if dryrun or verbose:
                print(f'{cube.name()} -> {new_name}')
            if not dryrun:
                cube.var_name = new_name
        elif dryrun or verbose:
            print(f'{cube.name()}')
        
        # Rename coords
        for coord in cube.coords():
            if coord in new_coordnames[0]:
                new_name = new_coordnames[1][new_coordnames[0].index(coord)]
                if not dryrun:
                    coord.var_name = new_name
                if dryrun or verbose:
                    print(f'    {new_name}')
            elif dryrun or verbose:
                print(f'  x {coord.name()}')
                
## TIMESTAMPS FROM FILENAMES
def umstamp_from_filename(filename):
    parts = filename.split('.')
    return parts[1][2:]

def filenames_to_datetimes(filenames, fmt='YYMDH'):
    datetimes = [um.convertFromUMStamp(umstamp_from_filename(file), fmt) for file in filenames]
    return np.array(datetimes)
    
def datetimes_to_timedeltas(datetimes):
    return file_dates[1:]-file_dates[0:-1]
    
def timedeltas_to_days(timedeltas):
    return np.array([td.days for td in timedeltas])

def plot_td_hist(td, frequency='Daily'):
    plt.hist(td, bins=np.arange(2.5, 30.5), log=True)
    plt.gcf().set_size_inches(15, 5)
    plt.xticks(np.arange(2, 31))
    plt.xlabel('Days')
    plt.ylabel('Number of timedeltas')
    plt.title(f'Distribution of times between filenames: {frequency}')
    plt.show()

def freq_hist_plot(filenames, frequency='Daily'):
    dtimes = filenames_to_datetimes(filenames)
    td = timedeltas_to_days(datetimes_to_timedeltas(dtimes))
    plot_td_hist(td, frequency=frequency)