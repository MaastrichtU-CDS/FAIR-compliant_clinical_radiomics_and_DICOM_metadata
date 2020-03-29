# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 10:46:39 2019

@author: Leonard Wee
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
import re
from datetime import datetime


inputPath = 'C:/seDI_lite/' #! PLS ADAPT THIS PATH
outputPath = 'C:/seDI_lite/autofill_ibsi_tables/' #! PLS ADAPT THIS PATH

myInstitution = 'maastro' #! PLS ADAPT THIS INSTITUTION HUMAN-READABLE LABEL
clinicalCollectionName = 'NSCLC-RADIOMICS-INTEROBSERVER1' #! THIS IS THE TCIA COLLECTION NAME
url_link_to_pyradiomics_latest = 'https://pyradiomics.readthedocs.io/en/latest/' #! THIS IS THE TCIA COLLECTION NAME

# we are going to partly hard-code some things and flexibly pull in others from the O-RAW pyradiomics CSV output


#import the extracted pyradiomics features from O-RAW; these should be some CSV file on the path selected above
inputFileOfExtractedFeaturesToProcessAsRdf = inputPath + 'nature_tcia_interobs_pyradiomics_2.2.2.csv'
featuresToProcess = pd.read_csv(inputFileOfExtractedFeaturesToProcessAsRdf).dropna()


"""
start by extracting the computed features, and changing the format to tall and narrow
"""
availableFeatures = list(featuresToProcess.columns.values.tolist())

features_idx = [i for i, f in enumerate(availableFeatures) if re.match(r'^original_',f)] #original
features_idx.extend([i for i, f in enumerate(availableFeatures) if re.match(r'^log.sigma',f)]) #laplacians
features_idx.extend([i for i, f in enumerate(availableFeatures) if re.match(r'^wavelet.',f)]) #wavelets
featuresLabels = [availableFeatures[i] for i in features_idx]
del(availableFeatures)

imagespace_df = featuresToProcess.iloc[:,0:3]

features = featuresToProcess.iloc[:,features_idx]

features.insert(0, 'patient', imagespace_df['patient'])
features.insert(1, 'struct_sop_instance_UID', imagespace_df['structUID'])
features.insert(2, 'mask_roi_name', imagespace_df['contour'])

feature_table = pd.melt(features,id_vars=["patient","struct_sop_instance_UID","mask_roi_name"],var_name ='Feature_name', value_name ='Value')
del(features_idx, features)


"""
Define IMAGESPACE - always generate or append IMAGESPACE IDs to an existing imagespace
which is the slightly dumb but safe way
use the imagespace_df panda crated above to generate imagespace IDs
"""
#imagespace_df

#if the ImageSpace_table already exists, add to it. If does not exist create it.
try:
    imgspace_table = pd.read_csv(outputPath + 'ImageSpace_table.csv').dropna()
except:
    #compose the output as an empty panda for the Software table CSV with these headers
    imgspace_table = pd.DataFrame(columns=['ImageSpace_name','ImageVolume_name','ROImask_name'])

#generate the linking id for image space
imgspace_name_list = imgspace_table['ImageSpace_name'].tolist()
pattern = re.compile(r'[0-9]+$')
try:
    results = list(map(int, [",".join(pattern.findall(item)) for item in imgspace_name_list]))
    newnumber = int( max( results )) + 1
except:
    newnumber = 1
del(imgspace_name_list,pattern, results)

#if the image space table was just created we will start number from ..._1, otherwise it will be the next
#consecutive integer higher than the previous maximum found

#create a list of image space names that will be every combination of listOfImageVolumeNames * listOfRoiMaskNames
imgspace = []
for i in range( len(imagespace_df) ):
    newname = '_'.join( ['ImageSpace',str(newnumber)] )
    imgspace.append( newname )
    newnumber = newnumber + 1
del(i,newnumber,newname)

imagespace_df.insert(0, 'ImageSpace_name', imgspace)
del(imgspace)
imagespace_df.insert(1, 'ImageVolume_name', imagespace_df['structUID'])
imagespace_df.insert(2, 'ROImask_name', imagespace_df['contour'])

imagespace_df = imagespace_df.drop(
        ["patient",
         "contour",
         "structUID"], axis=1)

#append to existing or empty imagespace table panda
imgspace_table = pd.concat([imgspace_table, imagespace_df],ignore_index=True)
del(imagespace_df)

#duplicates in the image space table get dropped and keep the first by default
imgspace_table.drop_duplicates(subset=["ImageVolume_name","ROImask_name"], inplace = True)
imgspace_table.to_csv(outputPath+'ImageSpace_table.csv', index = False)

#merge back into feature_table as the ImageSpace_name column
feature_table = pd.merge(feature_table,imgspace_table,how='left',
                left_on = ['struct_sop_instance_UID','mask_roi_name'],
                right_on = ['ImageVolume_name','ROImask_name'])
del(imgspace_table)

feature_table = feature_table.drop(
        ["struct_sop_instance_UID",
         "mask_roi_name",
         "ImageVolume_name",
         "ROImask_name"], axis=1)


"""
Define CALCULATIONRUNSPACE - always generate or append CALCULATIONRUNSPACE IDs to an
existing calc run space which is the slightly dumb but safe way

note this has a lower level reference to software space, so generate software space first

 -------------------------------- SOFTWARE TABLE FOR IBSI (above 3a)
"""
#currently only defined and tested for pyradiomic output parsed by Zhenwei Shi's ORAW package
software_label = 'pyradiomics'

#pyradiomics version should be in the panda of the imported features
pyradiomics_version_label = 'diagnostics_Versions_PyRadiomics' #PLS RE-DEFINE IF REQUIRED BY YOUR OUTPUT
pyradiomics_version_list = featuresToProcess[pyradiomics_version_label]
pyradiomics_version = set(pyradiomics_version_list)
if len(pyradiomics_version) > 1 :
    print("WARNING : Multiple pyradiomics versions detected in your input file.")
    exit()
if len(pyradiomics_version) < 1 :
    print("WARNING : No pyradiomics version detected in your input file.")
    exit()
pyradiomics_version = list(pyradiomics_version)[0]
#print(pyradiomics_version)
del(pyradiomics_version_label, pyradiomics_version_list)

#currently only defined and tested for Python output parsed by Zhenwei Shi's ORAW package
programming_language = 'python'
#
python_version_label = 'diagnostics_Versions_Python'
python_version_list = featuresToProcess[python_version_label]
python_version = set(python_version_list)
if len(python_version) > 1 :
    print("WARNING : Multiple python versions detected in your input file.")
    exit()
if len(python_version) < 1 :
    print("WARNING : No python version detected in your input file.")
    exit()
programming_language = '_'.join([ 'python', list(python_version)[0] ] ) #works for a single element set
#print(programming_language)
del(python_version, python_version_label, python_version_list)

#if the Software_table exists, assume it is current and use a matching entry. If does not exist create it :
try:
    software_table = pd.read_csv(outputPath + 'Software_table.csv').dropna()
    #match on pyradiomics_version, programming_language and myInstitution
    match = software_table.loc[
            (software_table['Version'] == pyradiomics_version) & 
            (software_table['ProgrammingLanguage'] == programming_language) &
            (software_table['Institution'] == myInstitution)
            ]
    if len(match) > 1:
        raise Exception('Error looking up Software_table.csv')
    elif len(match) < 1:
        #there is a table but not matching
        software_name_list = software_table['Software_name'].tolist()
        pattern = re.compile(r'[0-9]+$')
        results = list(map(int, [",".join(pattern.findall(item)) for item in software_name_list]))
        newnumber = int( max( results )) + 1
        software_name = '_'.join( ['Software', str(newnumber)] )
        software_table = software_table.append({'Software_name' : software_name,
                       'Software_label' : software_label,
                       'Version' : pyradiomics_version,
                       'ProgrammingLanguage' : programming_language,
                       'Institution' : myInstitution,
                       'Software_descriptor_metadata' : url_link_to_pyradiomics_latest} , ignore_index=True)
        software_table.to_csv(outputPath+'Software_table.csv', index = False)
        del(software_name_list, pattern, newnumber)
    else:
        software_name = match['Software_name'].values.tolist()[0] #there is a match
    del(match)
except:
    #compose the output as an empty panda for the Software table CSV with these headers
    software_table = pd.DataFrame(columns=['Software_name','Software_label','Version','ProgrammingLanguage','Institution','Software_descriptor_metadata'])
    software_name = '_'.join( ['Software', str(1)] )
    software_table = software_table.append({'Software_name' :  software_name,
                       'Software_label' : software_label,
                       'Version' : pyradiomics_version,
                       'ProgrammingLanguage' : programming_language,
                       'Institution' : myInstitution,
                       'Software_descriptor_metadata' : url_link_to_pyradiomics_latest} , ignore_index=True)
    software_table.to_csv(outputPath+'Software_table.csv', index = False)
del(programming_language, pyradiomics_version,software_label)
del(software_table)

"""
combine the software name id into the calculation run id
"""
#needs software_name variable from above
#software_name

#for now we are just going to generate a dummy UTC time
now = datetime.now() # current date and time
now_utc = str(datetime.timestamp(now)) #! ALTERNATIVE IS TO ENTER A KNOWN DATE AND TIME BY YOURSELF
del(now)

#if the CalculationRun_table exists, add to it. If does not exist create it
try:
    calcrun_table = pd.read_csv(outputPath + 'CalculationRunSpace_table.csv', dtype={'TimeStamp': object}).dropna()
    #match on timestamp and software name
    match = calcrun_table.loc[
            (calcrun_table['TimeStamp'] == now_utc) & 
            (calcrun_table['Software_name'] == software_name)
            ]
    if len(match) > 1:
        raise Exception('Error looking up CalculationRunSpace_table.csv')
    elif len(match) < 1:
        #there is a table but not matching
        calcrun_name_list = calcrun_table['CalculationRunSpace_name'].tolist()
        pattern = re.compile(r'[0-9]+$') 
        results = list(map(int, [",".join(pattern.findall(item)) for item in calcrun_name_list]))
        newnumber = int( max( results )) + 1
        calcrun_space_name = '_'.join( ['CalculationRunSpace', str(newnumber)] )
        calcrun_table = calcrun_table.append({'CalculationRunSpace_name' : calcrun_space_name,
                                          'TimeStamp' : now_utc,
                                          'Software_name' : software_name} , ignore_index=True)
        calcrun_table.to_csv(outputPath+'CalculationRunSpace_table.csv', index = False)
        del(calcrun_name_list, pattern, newnumber)
    else:
        calcrun_space_name = match['CalculationRunSpace_name'].values.tolist()[0] #there is a match
    del(match)
except:
    #compose the output as an empty panda for the Software table CSV with these headers
    calcrun_table = pd.DataFrame(columns=['CalculationRunSpace_name','TimeStamp','Software_name'])
    calcrun_space_name = '_'.join( ['CalculationRunSpace', str(1)] )
    calcrun_table = calcrun_table.append({'CalculationRunSpace_name' : calcrun_space_name,
                                          'TimeStamp' : now_utc,
                                          'Software_name' : software_name} , ignore_index=True)
    calcrun_table.to_csv(outputPath+'CalculationRunSpace_table.csv', index = False)
del(now_utc, calcrun_table)

#! append this Calculation Run ID column to the right side of the feature_table panda
feature_table.insert(4, 'CalculationRunSpace_name', calcrun_space_name)


"""
To define the FeatureParameterSpace ID as a unique ID corresponding to every combination of
        2a. Aggregation parameter, 3D, 3Davg etc
        2b. ImageFilterSpace ID as a unique ID corresponding to
        2c. InterpolationParameters as a unique ID corresponding to
        2d. ReSegmentationParameters as a unique ID corresponding to
        2e. DiscretisationParameters as a unique ID
        2f. FeatureSpecificParameters as a unique ID
"""

"""
--------------- FeatureSpecificParameters as a unique ID
"""
#generate feature specific definition matrix for pyradiomics
#if the FeatureSpecificParameters_table exists, use it.
#only create tf does not already exist
try:
    featspecparams_table = pd.read_csv(outputPath + 'FeatureSpecificParameters_table.csv')
except:
    #compose the output as an empty panda for the Software table CSV with these headers
    featspecparams_table = pd.DataFrame(columns=['FeatureSpecificParameters_name',
                                                 'morphParameters_name',
                                                 'glcmParameters_name',
                                                 'glrlmParameters_name',
                                                 'gldzmParameters_name',
                                                 'ngtdmParameters_name',
                                                 'ngldmParameters_name',
                                                 'intVolHistParameters_name' 
                                                 ])
    #to generate URLS, the element is always preceded by https://pyradiomics.readthedocs.io/en/latest/features.html
    pyradiomicsDefinitionTemplate = [
            'morphDefaultPyradiomicParameters_1',
            'glcmDefaultPyradiomicParameters_1',
            'glrlmDefaultPyradiomicParameters_1',
            'gldzmDefaultPyradiomicParameters_1',
            'ngtdmDefaultPyradiomicParameters_1',
            '',
            'intVolHistDefaultPyradiomicParameters_1']
    featspecparams_name = []
    newnumber = 1
    for i in pyradiomicsDefinitionTemplate:
        newname = '_'.join( ['FeatureSpecificParameters',str(newnumber)] )
        featspecparams_name.append( newname )
        newnumber = newnumber + 1
    del(i,newnumber,newname)
    #
    p = np.diag(pyradiomicsDefinitionTemplate)
    p = np.c_[featspecparams_name,p]
    #create the panda to be appended to the existing one
    temp = pd.DataFrame(p, columns=featspecparams_table.columns.values.tolist())
    del(p)
    #append to existing or empty imagespace table panda
    featspecparams_table = pd.concat([featspecparams_table, temp],ignore_index=True)
    temp.to_csv(outputPath+'FeatureSpecificParameters_table.csv', index = False)
    del(temp,featspecparams_name)

#! strictly assuming the DEFAULT pyradiomics feature definitions are applied, then generate the following default tables
#
#morph
try:
    morphParametersTable = pd.read_csv(outputPath + 'morphParameters_table.csv')
except:
    morphDefaultParameters = pd.DataFrame(
            [[pyradiomicsDefinitionTemplate[0],'','']],
            columns=['morphParameters_name','Method','Value'])
    morphDefaultParameters.to_csv(outputPath+'morphParameters_table.csv', index = False)
#
#glcm
try:
    glcmParametersTable = pd.read_csv(outputPath + 'glcmParameters_table.csv')
except:
    glcmDefaultParameters = pd.DataFrame(
            [[pyradiomicsDefinitionTemplate[1],'SYM','Chebychev','1','','']],
            columns=['glcmParameters_name','glcm_symmetry','DistanceNorm_method',
                     'DistanceNorm_value','DistanceNorm_unit','DistanceWeighting_function'])
    glcmDefaultParameters.to_csv(outputPath+'glcmParameters_table.csv', index = False)
#
#glrlm
try:
    glrlmParametersTable = pd.read_csv(outputPath + 'glrlmParameters_table.csv')
except:
    glrlmDefaultParameters = pd.DataFrame(
            [[pyradiomicsDefinitionTemplate[2],'']],
            columns=['glrlmParameters_name','DistanceWeighting_function'])
    glrlmDefaultParameters.to_csv(outputPath+'glrlmParameters_table.csv', index = False)
#
#gldzm
try:
    gldzmParametersTable = pd.read_csv(outputPath + 'gldzmParameters_table.csv')
except:
    gldzmDefaultParameters = pd.DataFrame(
            [[pyradiomicsDefinitionTemplate[3],'Chebychev','1','']],
            columns=['glrlmParameters_name','DistanceNorm_method','DistanceNorm_value','DistanceNorm_unit'])
    gldzmDefaultParameters.to_csv(outputPath+'gldzmParameters_table.csv', index = False)
#
#ngtdm
try:
    ngtdmParametersTable = pd.read_csv(outputPath + 'ngtdmParameters_table.csv')
except:
    ngtdmDefaultParameters = pd.DataFrame(
            [[pyradiomicsDefinitionTemplate[4],'Chebychev','1','','']],
            columns=['ngtdmParameters_name','DistanceNorm_method','DistanceNorm_value','DistanceNorm_unit','DistanceWeighting_function'])
    ngtdmDefaultParameters.to_csv(outputPath+'ngtdmParameters_table.csv', index = False)
#
#firstorder
try:
    intVolHistParametersTable = pd.read_csv(outputPath + 'intVolHistParameters_table.csv')
except:
    intVolHistDefaultParameters = pd.DataFrame(
            [[pyradiomicsDefinitionTemplate[6],'','HU','','HU']],
            columns=['intVolHistParameters_name','intVolHist_MinBound_value','intVolHist_MinBound_unit','intVolHist_MaxBound_value','intVolHist_MaxBound_unit'])
    intVolHistDefaultParameters.to_csv(outputPath+'intVolHistParameters_table.csv', index = False)


FeatureSpecificParameters_ID = ['']*len(featuresLabels)
for i, f in enumerate(featuresLabels):
    if re.match(r'^.*_shape_',f): #morphology features
        FeatureSpecificParameters_ID[i] = featspecparams_table['FeatureSpecificParameters_name'][0] #reference to morphology definition
    if re.match(r'^.*_glcm_',f): #glcm features
        FeatureSpecificParameters_ID[i] = featspecparams_table['FeatureSpecificParameters_name'][1] #reference to glcm definition
    if re.match(r'^.*_glszm_',f): #glszm features
        FeatureSpecificParameters_ID[i] = featspecparams_table['FeatureSpecificParameters_name'][2] #reference to glszm definition
    if re.match(r'^.*_glrlm_',f): #glrlm features
        FeatureSpecificParameters_ID[i] = featspecparams_table['FeatureSpecificParameters_name'][2] #reference to glrlm definition
    if re.match(r'^.*_gldm_',f): #gldm features
        FeatureSpecificParameters_ID[i] = featspecparams_table['FeatureSpecificParameters_name'][3] #reference to gldm definition
    if re.match(r'^.*_ngtdm_',f): #ngtdm features
        FeatureSpecificParameters_ID[i] = featspecparams_table['FeatureSpecificParameters_name'][4] #reference to ngtdm definition
    if re.match(r'^.*_ngldm_',f): #ngldm #! which is not defined in pyradiomics
        FeatureSpecificParameters_ID[i] = '' #reference to ngldm definition
    if re.match(r'^.*_firstorder_',f): #firstorder features
        FeatureSpecificParameters_ID[i] = featspecparams_table['FeatureSpecificParameters_name'][6] #reference to intensity features definition
d = {'Feature_name':featuresLabels,'FeatureSpecificParameters_name':FeatureSpecificParameters_ID}
FeatureParameterSpace_df = pd.DataFrame(d) #assembling this lookup will be essential to 
del(d,FeatureSpecificParameters_ID, i,f)
del(featspecparams_table)


#--------------- Discretization parameters as a literal entry
#generate discretization definitions for pyradiomics
DiscretizationParameters_ID = ['']*len(featuresLabels)
for i, f in enumerate(featuresLabels):
    if re.match(r'^original_',f):
        DiscretizationParameters_ID[i] = 'DiscretisationParameters_1' #FixedBinWidth_0.5
    if re.match(r'^log.sigma',f):
        DiscretizationParameters_ID[i] = 'DiscretisationParameters_2' #FixedBinWidth_10
    if re.match(r'^wavelet.',f):
        DiscretizationParameters_ID[i] = 'DiscretisationParameters_3' #FixedBinWidth_5
    if re.match(r'^original_shape',f):
        DiscretizationParameters_ID[i] = ''
FeatureParameterSpace_df.insert(1, 'DiscretisationParameters', DiscretizationParameters_ID)
del(f,i)
del(DiscretizationParameters_ID)
#create a DiscretisationParameters_table for the pyradiomics defaults
#DiscretisationParameters_table
try:
    DiscretisationParameters = pd.read_csv(outputPath + 'DiscretisationParameters_table.csv')
except:
    DiscretisationParameters = pd.DataFrame(
            [['DiscretisationParameters_1','','FBSequal','0.5','HU','0','HU'],
             ['DiscretisationParameters_2','','FBSequal','10','HU','0','HU'],
             ['DiscretisationParameters_3','','FBSequal','5','HU','0','HU']],
            columns=['DiscretisationParameters_name',
                     'Equalisation_NumberOfBins_value',
                     'Algorithm','Value','Unit',
                     'Discretisation_min_value',
                     'Discretisation_min_unit'])
    DiscretisationParameters.to_csv(outputPath+'DiscretisationParameters_table.csv', index = False)

#--------------- Resegmentation parameters as a literal entry
#generate discretization definitions for pyradiomics
ResegmentationParameters_ID = ['ReSegmentationParameters_1']*len(featuresLabels)
for i, f in enumerate(featuresLabels):
    if re.match(r'^original_shape',f):
        ResegmentationParameters_ID[i] = ''
FeatureParameterSpace_df.insert(1, 'ReSegmentationParameters', ResegmentationParameters_ID)
del(f,i)
del(ResegmentationParameters_ID)
#create a ReSegmentationParameters_table for the pyradiomics defaults
#ReSegmentationParameters_table
try:
    ResegmentationParameters = pd.read_csv(outputPath + 'ReSegmentationParameters_table.csv')
except:
    ResegmentationParameters = pd.DataFrame(
            [['ReSegmentationParameters_1','','HU','','HU','3']],
            columns=['ReSegmentationParameters_name',
                     'ReSegmentationRange_min_value',
                     'ReSegmentationRange_min_unit',
                     'ReSegmentationRange_max_value',
                     'ReSegmentationRange_max_unit',
                     'OutlierRemoval_threshold'])
    ResegmentationParameters.to_csv(outputPath+'ReSegmentationParameters_table.csv', index = False)

#--------------- Interpolation parameters as a literal entry
#generate interpolation definitions for pyradiomics
InterpolationParameters_ID = ['InterpolationParameters_1']*len(featuresLabels)
for i, f in enumerate(featuresLabels):
    if re.match(r'^original_shape',f):
        InterpolationParameters_ID[i] = ''
FeatureParameterSpace_df.insert(1, 'InterpolationParameters', InterpolationParameters_ID)
del(f,i)
del(InterpolationParameters_ID)
#create a InterpolationParameters_table for the pyradiomics defaults
#InterpolationParameters_table
try:
    InterpolationParameters = pd.read_csv(outputPath + 'InterpolationParameters_table.csv')
except:
    InterpolationParameters = pd.DataFrame(
            [['InterpolationParameters_1','2','mm','LIN','','HU','','']],
            columns=['InterpolationParameters_name',
                     'Value',
                     'Unit',
                     'ImageVolume_method',
                     'ImageVolume_GreyLevelRound_value',
                     'ImageVolume_GreyLevelRound_unit',
                     'ROImask_method',
                     'ROImask_PartialVolumeCutoff_value'])
    InterpolationParameters.to_csv(outputPath+'InterpolationParameters_table.csv', index = False)


#--------------- Image Filter parameters as a literal entry
#generate image filter definitions for pyradiomics
#--- I think it would be much nicer to interrogate this from the feature names in pyradiomics and match by merge
#--- but not yet implemented
ImageFilterSpace_ID = ['']*len(featuresLabels)
for i, f in enumerate(featuresLabels):
    if re.match(r'^wavelet.LLL',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_1'
    if re.match(r'^wavelet.LLH',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_2'
    if re.match(r'^wavelet.LHL',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_3'
    if re.match(r'^wavelet.LHH',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_4'
    if re.match(r'^wavelet.HLL',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_5'
    if re.match(r'^wavelet.HLH',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_6'
    if re.match(r'^wavelet.HHL',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_7'
    if re.match(r'^wavelet.HHH',f):
        ImageFilterSpace_ID[i] = 'ImageFilterSpace_8'
    if re.match(r'^log.sigma.1.0.mm.3D',f):
        ImageFilterSpace_ID[i] = 'LaplacianOfGaussian1mmWidth' #LaplacianOfGaussian_1mmWidth
    if re.match(r'^log.sigma.2.0.mm.3D',f):
        ImageFilterSpace_ID[i] = 'LaplacianOfGaussian2mmWidth' #LaplacianOfGaussian_2mmWidth
    if re.match(r'^log.sigma.3.0.mm.3D',f):
        ImageFilterSpace_ID[i] = 'LaplacianOfGaussian3mmWidth' #LaplacianOfGaussian_3mmWidth
FeatureParameterSpace_df.insert(1, 'ImageFilterSpaceParameters', ImageFilterSpace_ID)
del(f,i)
del(ImageFilterSpace_ID)
#
#image filter space table
try:
    ImageFilterSpace = pd.read_csv(outputPath + 'ImageFilterSpace_table.csv')
except:
    ImageFilterSpace = pd.DataFrame(
            [['ImageFilterSpace_1','WaveletFilter_1'],
             ['ImageFilterSpace_2','WaveletFilter_2'],
             ['ImageFilterSpace_3','WaveletFilter_3'],
             ['ImageFilterSpace_4','WaveletFilter_4'],
             ['ImageFilterSpace_5','WaveletFilter_5'],
             ['ImageFilterSpace_6','WaveletFilter_6'],
             ['ImageFilterSpace_7','WaveletFilter_7'],
             ['ImageFilterSpace_8','WaveletFilter_8']],
            columns=['ImageFilterSpace_name','WaveletFilterParameters_name'])
    ImageFilterSpace.to_csv(outputPath+'ImageFilterSpace_table.csv', index = False)
#
#wavelet filter parameters table
try:
    WaveletFilterParameters = pd.read_csv(outputPath + 'WaveletFilterParameters_table.csv')
except:
    WaveletFilterParameters = pd.DataFrame(
            [['WaveletFilter_1','coif1','LLL'],
             ['WaveletFilter_2','coif1','LLH'],
             ['WaveletFilter_3','coif1','LHL'],
             ['WaveletFilter_4','coif1','LHH'],
             ['WaveletFilter_5','coif1','HLL'],
             ['WaveletFilter_6','coif1','HLH'],
             ['WaveletFilter_7','coif1','HHL'],
             ['WaveletFilter_8','coif1','HHH']],
            columns=['WaveletFilterParameters_name','BasisFunction','WaveletDirection'])
    WaveletFilterParameters.to_csv(outputPath+'WaveletFilterParameters_table.csv', index = False)


#--------------- Aggregation parameters as a literal entry
#generate aggregation definitions for pyradiomics
AggregationSpace_ID = ['']*len(featuresLabels)
for i, f in enumerate(featuresLabels):
    if re.match(r'^.*_shape_',f):
        AggregationSpace_ID[i] = '3D'
    if re.match(r'^.*_firstorder_',f):
        AggregationSpace_ID[i] = '3D'
    if re.match(r'^.*_glcm_',f):
        AggregationSpace_ID[i] = '3Davg'
    if re.match(r'^.*_glrlm_',f):
        AggregationSpace_ID[i] = '3Davg'
    if re.match(r'^.*_glszm_',f):
        AggregationSpace_ID[i] = '3D'
    if re.match(r'^.*_gldm_',f):
        AggregationSpace_ID[i] = '3D'        
    if re.match(r'^.*_ngtdm_',f):
        AggregationSpace_ID[i] = '3D'        
FeatureParameterSpace_df.insert(1, 'AggregationParameters', AggregationSpace_ID)
del(f,i)
del(AggregationSpace_ID)

#! if we now take the last six columns of the FeatureSpaceParameter panda, we could do a drop duplicate to
#! generate only the unique feature space parameter IDs needed in here
#
# as the files get larger it is probably more efficient to append to existing or new file first
# then prune duplicates and then finally merge back to define the required FeatureParameterSpace_name
FeatureParameterSpace_unique = FeatureParameterSpace_df.iloc[:,1:7]
FeatureParameterSpace_unique.drop_duplicates(
        subset=["AggregationParameters",
                "ImageFilterSpaceParameters",
                "InterpolationParameters",
                "ReSegmentationParameters",
                "DiscretisationParameters",
                "FeatureSpecificParameters_name",
                ],
        inplace = True)
fps = []
for i in range( len(FeatureParameterSpace_unique) ):
    newname = '_'.join( ['FeatureParameterSpace',str(i+1)] )
    fps.append( newname )
del(i,newname)
FeatureParameterSpace_unique.insert(0,'FeatureParameterSpace_name',fps)
del(fps)

#concatenate existing (or newly created) FeatureParameterSpace_table with the one generated above
#then drop duplicates keeping the earlier occurrence
try:
    featparaspace_table = pd.read_csv(outputPath + 'FeatureParameterSpace_table.csv',keep_default_na=False)
except:
    featparaspace_table = pd.DataFrame(columns=['FeatureParameterSpace_name',
                                                 'AggregationParameters',
                                                 'ImageFilterSpaceParameters',
                                                 'InterpolationParameters',
                                                 'ReSegmentationParameters',
                                                 'DiscretisationParameters',
                                                 'FeatureSpecificParameters_name' 
                                                 ])

#append to existing or empty imagespace table panda
featparaspace_table = pd.concat([featparaspace_table, FeatureParameterSpace_unique],ignore_index=True)
del(FeatureParameterSpace_unique)

#duplicates in the appended FeatureParameterSpace_table get dropped and keep the first by default
featparaspace_table.drop_duplicates(subset=["AggregationParameters",
                "ImageFilterSpaceParameters",
                "InterpolationParameters",
                "ReSegmentationParameters",
                "DiscretisationParameters",
                "FeatureSpecificParameters_name",
                ], inplace = True)
#write back to filesystem as the updated FeatureParameterSpace_table
featparaspace_table.to_csv(outputPath+'FeatureParameterSpace_table.csv', index = False)

#merge back into FeatureParameterSpace)df to find assign the correct IDs to the individual features!
FeatureParameterSpace_Dictionary = pd.merge(FeatureParameterSpace_df,featparaspace_table,how='left',on=None)

#add IBSI nomenclature to the FeatureParameterSpace_Dictionary
# ----- read from provided stem dictionary
pyradiomics_stemnames = pd.read_csv(inputPath + 'stemname_PyRadiomicsFeatures_With_Units.csv')
# ----- search and replace for the stem
current_names = FeatureParameterSpace_Dictionary['Feature_name'].str.split('_',expand=True)
FeatureParameterSpace_Dictionary['pyradiomics_stem'] = current_names.iloc[:,1:3].apply(lambda x: '_'.join(x), axis=1)
del current_names
# ----- merge back to dictionary panda with pyradiomics_stem_name, IBSI_Feature_name and Unit
temp = pd.merge(FeatureParameterSpace_Dictionary, pyradiomics_stemnames,
         how = 'left',
         left_on = ['pyradiomics_stem'],
         right_on = ['Pyradiomics_Stem_Name']
         )
FeatureParameterSpace_Dictionary = temp.drop(['pyradiomics_stem','Pyradiomics_Stem_Name'],axis=1)
del temp
FeatureParameterSpace_Dictionary.to_csv(outputPath+'feature_parameter_space_dictionary.csv', index = False)
del(FeatureParameterSpace_df,featparaspace_table) 


#use the feature parameter space dictionary now to match to features for the last part of the feature_table
temp = pd.merge(feature_table,FeatureParameterSpace_Dictionary,
         how='left',
         left_on = ['Feature_name'],
         right_on = ['Feature_name']
         )
del(feature_table,FeatureParameterSpace_Dictionary)

#drop out the unnecessary columns for the feature table
temp = temp.drop(["AggregationParameters","ImageFilterSpaceParameters",
                  "InterpolationParameters","ReSegmentationParameters",
                  "DiscretisationParameters","FeatureSpecificParameters_name"], axis=1)

#reorder columns
temp = temp[['patient','IBSI_Feature_Name','Value','Unit','ImageSpace_name','FeatureParameterSpace_name','CalculationRunSpace_name']]

#insert a patient label column - this is the name of the collection on The Cancer Imaging Archive
temp.insert(1,'Patient_label',clinicalCollectionName)

#set the correct names for the dataframe columns
temp.columns = ['PatientID', 'Patient_label', 'Feature_name', 'Value', 'Unit',
                'ImageSpace_name','FeatureParameterSpace_name', 'CalculationRunSpace_name']

#write the final result out to file :
temp.to_csv(outputPath+clinicalCollectionName+'_Feature_table.csv', index = False)

del(featuresToProcess, temp)


