import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import math
import numpy as np

#-------------------------------------------------------------------------------
#
# AutoTransparency
#
#-------------------------------------------------------------------------------
class AutoTransparency(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "AutoTransparency"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Vinyas Harish, Tamas Ungi, Andras Lasso (PerkLab, Queen's)"]
    self.parent.helpText = """
    Prevent the occlusion of a model by adaptively changing the transparency of
    other models in the scene.
    """
    self.parent.acknowledgementText = """
    This work was was funded by Cancer Care Ontario, the Ontario Consortium for
    Adaptive Interventions in Radiation Oncology (OCAIRO)"""

#-------------------------------------------------------------------------------
#
# AutoTransparencyWidget
#
#-------------------------------------------------------------------------------
class AutoTransparencyWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # Input target model selector
    #
    self.targetSelector = slicer.qMRMLNodeComboBox()
    self.targetSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.targetSelector.selectNodeUponCreation = False
    self.targetSelector.addEnabled = True
    self.targetSelector.removeEnabled = True
    self.targetSelector.noneEnabled = True
    self.targetSelector.showHidden = False
    self.targetSelector.showChildNodeTypes = False
    self.targetSelector.setMRMLScene( slicer.mrmlScene )
    self.targetSelector.setToolTip( "Pick the target model node." )
    parametersFormLayout.addRow("Target model: ", self.targetSelector)

    #
    # Input moving model selector
    #
    self.movingModelSelector = slicer.qMRMLNodeComboBox()
    self.movingModelSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.movingModelSelector.selectNodeUponCreation = True
    self.movingModelSelector.addEnabled = True
    self.movingModelSelector.removeEnabled = True
    self.movingModelSelector.noneEnabled = True
    self.movingModelSelector.showHidden = False
    self.movingModelSelector.showChildNodeTypes = False
    self.movingModelSelector.setMRMLScene( slicer.mrmlScene )
    self.movingModelSelector.setToolTip( "Pick the moving model node (the model "
      "that will have their transparency dynamically changed).")
    parametersFormLayout.addRow("Moving model: ", self.movingModelSelector)

    #
    # Check box to enable autotransparency throughout Slicer
    #
    self.enableAutoTransparencyFlagCheckBox = qt.QCheckBox()
    self.enableAutoTransparencyFlagCheckBox.checked = 0
    self.enableAutoTransparencyFlagCheckBox.setToolTip("If checked, enable AutoTransparency.")
    parametersFormLayout.addRow("Enable AutoTransparency", self.enableAutoTransparencyFlagCheckBox)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

#-------------------------------------------------------------------------------
#
# AutoTransparencyLogic
#
#-------------------------------------------------------------------------------

class AutoTransparencyLogic(ScriptedLoadableModuleLogic):
  def logicMethod(self):
    pass


#-------------------------------------------------------------------------------
#
# AutoTransparencyTest
#
#-------------------------------------------------------------------------------
class AutoTransparencyTest(ScriptedLoadableModuleTest):
  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_AutoTransparency()

  def test_AutoTransparency(self):
    self.delayDisplay("Starting the test")

    #Create a cautery model
    moduleDirectoryPath = slicer.modules.autotransparency.path.replace('AutoTransparency.py', '')
    slicer.util.loadModel(qt.QDir.toNativeSeparators(moduleDirectoryPath + 'Resources/CAD/Cautery.stl'))
    cauteryModelNode = slicer.util.getNode(pattern = "Cautery")
    cauteryModelNode.GetDisplayNode().SetColor(1.0, 1.0, 0)
    cauteryModelNode.SetName("CauteryModel")
    cauteryModelNode.GetDisplayNode().SliceIntersectionVisibilityOn()

    #Create transform node and set transform of transform node
    cauteryModelToRas = slicer.vtkMRMLLinearTransformNode()
    cauteryModelToRas.SetName('CauteryModelToRas')
    slicer.mrmlScene.AddNode(cauteryModelToRas)
    cauteryModelToRasTransform = vtk.vtkTransform()
    cauteryModelToRasTransform.PreMultiply()
    cauteryModelToRasTransform.Translate(0, 100, 0)
    cauteryModelToRasTransform.RotateX(30)
    cauteryModelToRasTransform.Update()
    cauteryModelToRas.SetAndObserveTransformToParent(cauteryModelToRasTransform)

    #Transform the needle model
    cauteryModelNode.SetAndObserveTransformNodeID(cauteryModelToRas.GetID())

    #Create a sphere tumor model
    tumorModelNode = slicer.modules.createmodels.logic().CreateSphere(10)
    tumorModelNode.GetDisplayNode().SetColor(0,1,0) #Green
    tumorModelNode.SetName('TumorModel')

    #Create transform node and set transform of transform node
    tumorModelToRas = slicer.vtkMRMLLinearTransformNode()
    tumorModelToRas.SetName('tumorModelToRas')
    slicer.mrmlScene.AddNode(tumorModelToRas)
    tumorModelToRasTransform = vtk.vtkTransform()
    tumorModelToRas.SetAndObserveTransformToParent(tumorModelToRasTransform)

    #Transform the tumor model
    tumorModelNode.SetAndObserveTransformNodeID(tumorModelToRas.GetID())

    #Compute the center of mass of the target model node
    tumorModel = slicer.mrmlScene.GetNodeByID('vtkMRMLModelNode5')
    tumorModelPolyData = tumorModel.GetPolyData()
    centerFilter = vtk.vtkCenterOfMass()
    centerFilter.SetInputData(tumorModelPolyData)
    centerFilter.SetUseScalarsAsWeights(False)
    centerFilter.Update()

    #Transform center to RAS coordinate system
    center = []
    for i,val in enumerate(centerFilter.GetCenter()):
      center.append(val)

    center.append(1.0)
    tumorModelToRas_transformNode = slicer.mrmlScene.GetNodeByID('vtkMRMLLinearTransformNode5')
    tumorModelToRas_vtkMatrix = vtk.vtkMatrix4x4()
    tumorModelToRas_transformNode.GetMatrixTransformToParent(tumorModelToRas_vtkMatrix)
    tumorModelToRas_vtkMatrix.MultiplyPoint(center,center)
    center.remove(1.0)
    print "Center of mass in RAS: ", center

    #Get the camera node's position
    cam = slicer.util.getNode('vtkMRMLCameraNode1')
    pos = [0.0,0.0,0.0]
    cam.GetPosition(pos)
    print "Camera position: ", pos

    #Find dMax
    dMax = 0
    numPoints = tumorModelPolyData.GetNumberOfPoints()
    pointTupleArray = []
    #Create array of all points that make up the model
    for point in range(numPoints):
      pointTupleArray.append(tumorModelPolyData.GetPoint(point))

    for point in pointTupleArray:
      dist = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(point,center))
      if (dist > dMax):
        dMax = dist

    #Find the angle, alpha
    l = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(pos,center))
    alpha = math.asin(dMax/l)

    #Find the radius of the cone, based on triangle 2
    height = l
    radius = (math.tan(alpha))*(height)

    #Create a model of the cone and visualize it in the scene
    cone = vtk.vtkConeSource()
    cone.SetRadius(radius)
    cone.SetHeight(height)
    cone.SetCenter(center)
    cone.SetResolution(10)

    coneModelNode = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(coneModelNode)
    coneModelNode.SetName('ConeModel')
    coneModelNodeToUpdate = coneModelNode
    cone.Update()
    coneModelNodeToUpdate.SetAndObservePolyData(cone.GetOutput())

    if coneModelNodeToUpdate.GetDisplayNode() is None:
      displayNode = slicer.vtkMRMLModelDisplayNode()
      slicer.mrmlScene.AddNode(displayNode)
      displayNode.SetName('ConeModelDisplay')
      coneModelNodeToUpdate.SetAndObserveDisplayNodeID(displayNode.GetID())

    #Find the tip of cone and the center of the base of the cone, points which
    #will be used as inputs for the landmark registration
    coneModelPolyData = coneModelNode.GetPolyData()
    numPointsInCone = coneModelPolyData.GetNumberOfPoints()
    conePointsTupleArray = []
    for point in range(numPointsInCone):
      conePointsTupleArray.append(coneModelPolyData.GetPoint(point))
    coneTip = conePointsTupleArray[0]
    #Place fiducial at cone tip
    markupsLogic = slicer.modules.markups.logic()
    markupsLogic.SetDefaultMarkupsDisplayNodeGlyphScale(5.0)
    markupsLogic.SetDefaultMarkupsDisplayNodeColor(0.0, 0.0, 0.0)
    markupsLogic.SetDefaultMarkupsDisplayNodeSelectedColor(0.0, 0.0, 0.0)
    markupsLogic.AddNewFiducialNode()
    markupsLogic.AddFiducial(coneTip[0], coneTip[1], coneTip[2])
    fidList = slicer.util.getNode('F')
    fidList.SetNthFiducialLabel(0, 'Cone Tip')

    #Compute center of mass of points of cone base
    coneBasePoints = []
    for index in range(1, numPointsInCone):
      point = conePointsTupleArray[index]
      coneBasePoints.append(point)
    xSum, ySum, zSum = 0, 0, 0
    for (x,y,z) in coneBasePoints:
      xSum += x
      ySum += y
      zSum += z
    coneBaseCenter_x = xSum / cone.GetResolution()
    coneBaseCenter_y = ySum / cone.GetResolution()
    coneBaseCenter_z = zSum / cone.GetResolution()
    #Place fiducial at cone base
    markupsLogic.AddFiducial(coneBaseCenter_x, coneBaseCenter_y, coneBaseCenter_z)
    fidList.SetNthFiducialLabel(1, 'Cone Base Center')

    #Create a third point for use in landmark registration, perpendicular to a
    #line drawn in the AP plane of the cone tip
    pointCoplanarToConeTip = (coneTip[0], coneTip[1] + 100 , coneTip[2]) #Add arbitrary distance along plane
    markupsLogic.AddFiducial(pointCoplanarToConeTip[0],pointCoplanarToConeTip[1],pointCoplanarToConeTip[2])
    midpointOfConeTipLine = ((coneTip[0] + pointCoplanarToConeTip[0])/2 , (coneTip[1] + pointCoplanarToConeTip[1])/2, (coneTip[2] + pointCoplanarToConeTip[2])/2)
    markupsLogic.AddFiducial(midpointOfConeTipLine[0],midpointOfConeTipLine[1],midpointOfConeTipLine[2])
    perpendicularPoint = (midpointOfConeTipLine[0], midpointOfConeTipLine[1], midpointOfConeTipLine[2] + 100)
    markupsLogic.AddFiducial(perpendicularPoint[0],perpendicularPoint[1],perpendicularPoint[2])


    self.delayDisplay('Test passed!')
