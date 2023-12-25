# netherland
Models below ground biomsass production and decomposition keeping track of sedimention in mophodynamic simulations of salt marshes.

This model follows closely the SEMIDEC Model described in:
> Morris, J. T., & Bowden, W. B. (1986). A Mechanistic, Numerical Model of Sedimentation, Mineralization, and Decomposition for Marsh Sediments. *Soil Science Society of America Journal*, 50(1), 96-105. https://doi.org/10.2136/sssaj1986.03615995005000010019x

## Use 

The model's basic unit of analysis is a singe grid cell. A simulation will evaluate one or many grid cells, but within the context of this model each cells is independent of the others.

The model is parameterized with a large number of constants, for each of the model's cells. These parameters are imported from a *.toml file, using the constants.import_file(filepath: str) command. A default file that provides the values presented in Table 1. Definitions and best estimates of parameters of Morris & Bowden (1986) is distributed with the package and will load as the default input ot the constants.import_file() command. 

Throughout a simulation, once per timstep the model takes exogenously input erosion/deposition values from a coupled sediment transport model, like those in the Delft3D software (https://oss.deltares.nl/web/delft3d); and above ground biomass values from vegitation model, like the NBSDynamics software (https://github.com/Deltares-research/NBSDynamics) [note: both are produced by Deltares (https://www.deltares.nl/en)]. The length of model timesteps, is also taken as an input - though the length of the model timesteps may vary thoughout the course of the simulation. 


## Assumptions

## Notes
Morris and Bowden (1986) describes a stable, marsh with constant levels of exogenous deposition and no erosion. This leads to the following assumptions:
1. Turnover of biomass due to erosion and burial can be apportioned as follows:
    
    Labile: (1 - k3)(1 - fc)R_u,b where R_u,b is the biomass between depths [u,b].
    Refractory: (1 - k3)(fc)R_u,b
    Inorganic: k3 x R_u,b
    
    This assumes below ground biomass contains k3 portion inorganic material. This asumption is supported by Equation 9 in Morris & Bowden (1986). It also assumes the remaing (1 - k3) portion of below ground biomass can be apportioned to organic labile (1 - fc) and refractory (fc) materials. This is supported by equations 5 and 6, which deal with turnover. However, Morris & Bowden assume that in turnover uptake and decomposition of inorganic ash in the below ground biomass cancel each other out, therefore only the refactory and labile portions of turnover need to be tracked. This cannot be assumed when below ground biomass leaves the system as erosion, or is turnover due to burial below the root zone.
