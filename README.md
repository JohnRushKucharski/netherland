# netherland
Models below ground biomsass production and decomposition keeping track of sedimention in morphodynamic simulations of salt marshes.

This model follows closely the SEMIDEC Model described in:
> Morris, J. T., & Bowden, W. B. (1986). A Mechanistic, Numerical Model of Sedimentation, Mineralization, and Decomposition for Marsh Sediments. *Soil Science Society of America Journal*, 50(1), 96-105. https://doi.org/10.2136/sssaj1986.03615995005000010019x

The model's basic unit of analysis is a cell, or block of sediment. A simulation may evaluate many cells, but within the context of this model each cells is independent of the others. Each cell is composed of a series of layers. Each layer contains live below ground biomass and stocks of labile, refractory and inorganic sediments, associated with a single simulated timestep.

![alt text](https://github.com/JohnRushKucharski/netherland/blob/main/img/cell.jpg?raw=true)

The cell is parameterized with a large number of constants. These parameters are imported from a *.toml file, using the constants.import_file(filepath: str) command. A default file that provides the values presented in Table 1. Definitions and best estimates of parameters of Morris & Bowden (1986) is distributed with the package and will load as the default input to the constants.import_file() command. 

Throughout a simulation, at the start of each simulated timestep coupled models provide sedimentation and biomass inputs for each grid cell. Specifically, erosion/deposition inputs are provided by a coupled sediment transport model, like those in the Delft3D software (https://oss.deltares.nl/web/delft3d); and above ground biomass inputs are provided by a vegitation model, like the NBSDynamics software (https://github.com/Deltares-research/NBSDynamics) [note: both are produced by Deltares (https://www.deltares.nl/en)]. The length of model timesteps, is also taken as an input - though the length of the model timesteps may vary thoughout the course of the simulation. 

## Compute Process
Once per timestep the model recieves inputs cooresponding to:

1. Deposition/erosion of sediment on each cell [in cm].

2. Concentration of below ground biomass at the cell's surface [in g/cm2].

3. Length of the simulated timestep [in yrs]. 

4. Optionally, the discrete timestep inputs can be equally divided into a specified number of sub-steps, so that the discrete timestep model better emulates a simulated continous time model. 

These inputs are supplied to the Cell.step_forward() function. The compute process in a layer-by-layer fashion, starting at the surface layer and proceeding downward (toward the bottom layer). Within each layer the following compute process is followed:

1. Turnover (gains), burial (transfers) and erosion (losses) of below ground biomass is computed. Erosion of biomass and burial due to deposition of sediment is a function of the deposition/erosion input. Turnover is specified in imported *.toml file constants.

2. Labile decomposition and inorganic uptake (losses) are taken into account. The rate of these processes is specified in the input *.toml file constants.

3. Turned over or buried biomsss computed in step one is added to the layers labile, refractory and inorganic stocks.

4. Erosion of labile, refractory and inorganic sediment (less erosion of below ground biomass accounted for in step 1) are taken into account. These values are a function of the deposition/erosion input.

5. If the top layer is being processed deposited sediment is added to the layer. Note, if the top layer is being proceessed then none of the processes in steps 1-4 occur (since prior to deposition no biomass or other sediment exists in the layer).

6. The new layer depth is computed taking steps 1-5 into account. This makes it possible to compute the amount of live below ground biomass that is present in the layer (since this depends on distribution parameters defined the the input *.toml constants file.)

## Assumptions
The following are notable assumptions, many arising from Morris & Bowden (1986). They are listed here in not particular order and this list is not exhustive.

1. The model is not a closed system. Specifically there both gains and losses from each cell. The following list summarizes the gains and losses:

a. Turnover of Belowground Biomass: live below ground biomass is assumed to turnover at the same (instantaneous) rate that it is replaced with the growth of new below ground biomass. Since the rate of growth/turnover is not contrained by any modeled stock, this results in a net gain to the system (cell).

b. Decomposition of Labile Sediment: labile sediment leave the system at a rate specified in the imported *.toml file.

c. Uptake of Inorganic Ash for Above Ground Biomass: Inorganic sediment (ash) leaves the cell (below ground sediment) at a rate specified in the *.toml file to support above ground plant production. Since this production is not modeled directly, it represents a net loss to the system. Inorganic sediment is also used to support the growth of belowground biomass but it the rate of below ground uptake and turnover are assumed to be equal.

d. Sediment and Biomass leave the system though exogenously modeled erosion, and sediment enters the system through exogenous deposition. Similiarly biomass enters the system through the exogenously provided concentrations of below ground biomass (as the surface of the marsh).

These assumptions are consistent with those found in Morris & Bowden (1986). The implication is that mass is not conserved within the model.

2. The model is a discrete time model. As a result the order of the compute process can have a large impact on the simulated results. The order of the compute process is explained above. A single timestep can be equally divided into a number of smaller substeps, in order to better emulate a continuous time process. However, this fundemental limitation of the model remains.

3. A layer is the minimum unit of analysis in the model. Although biomass, labile, refractory and inorganic stocks are tracked as components of a layer, no distinction is made regarding how these materials are distributed within the layer (either horizontally or vertically). This is noteable because though the amount of biomass is a function of depth, when turnover, deposition, erosion or any other layer level process occurs it affect the layer as whole and not any subset of that layer.

4. Below ground biomass does not grow (or survive) below the maximum root depth, specified in the input *.toml constants file. The implication of this assumption is that any live biomass which is "buried" below this specified depth is converted into labile, refractory and inorgainic sediment.

5. Below ground biomass always grows down to the maximum root depth, specified in the input *.toml constants file. The concentration of below ground biomass at various depths within the cell is controlled by the paramters of a exponential decay function (the concentration of biomass decreases with depth) and a maximum root depth (i.e. the root depth does not for instance depend on the age of the plants). Therefore, some positive (though possibly very small) concentration of biomass will be simulated for depths not exceeding the maximum depth of the root zone, even if the concentration at the surface is small or new.  