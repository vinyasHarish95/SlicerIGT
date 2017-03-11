import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import math
import collections
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

    #
    # Label to display if collisions are occuring or not
    #
    self.collisionWarningLabel = qt.QLabel("No models currently specified.")
    self.collisionWarningLabel.setStyleSheet('color: grey')
    self.layout.addWidget(self.collisionWarningLabel)

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
  #
  # Draw cone around target model
  #

  def computeCenterOfMass(self, modelPolyData):
    centerFilter = vtk.vtkCenterOfMass()
    centerFilter.SetInputData(modelPolyData)
    centerFilter.SetUseScalarsAsWeights(False)
    centerFilter.Update()
    return centerFilter

  def getCameraPosition(self):
    cameraNode = slicer.util.getNode('vtkMRMLCameraNode1')
    cameraPosition = [0.0,0.0,0.0]
    cameraNode.GetPosition(cameraPosition)
    return cameraPosition

  def computeConeDimensions(self, inputModelPolyData, inputCenterOfMass, cameraPosition):
    #Find dMax
    dMax = 0
    numPoints = inputModelPolyData.GetNumberOfPoints()
    pointTupleArray = []
    #Create array of all points that make up the model
    for point in range(numPoints):
      pointTupleArray.append(inputModelPolyData.GetPoint(point))

    for point in pointTupleArray:
      dist = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(point, inputCenterOfMass))
      if (dist > dMax):
        dMax = dist

    #Find the angle, alpha
    l = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(cameraPosition,inputCenterOfMass))
    alpha = math.asin(dMax/l)

    #Find the radius of the cone, based on triangle 2
    height = l
    radius = (math.tan(alpha))*(height)

    #Return dimensions as a named tuple
    ConeDimensions = collections.namedtuple('ConeDimensions', ['height', 'radius'])
    coneDimensions = ConeDimensions(height, radius)
    return coneDimensions

  def createConeSource(self, coneDimensions, center, resolution):
    coneSource = vtk.vtkConeSource()
    coneSource.SetRadius(coneDimensions.radius)
    coneSource.SetHeight(coneDimensions.height)
    coneSource.SetCenter(center)
    coneSource.SetResolution(resolution)
    return coneSource

  def drawCone(self, coneSource, coneDimensions, center):
    coneModelNode = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(coneModelNode)
    coneModelNode.SetName('ConeModel')
    coneModelNodeToUpdate = coneModelNode
    coneSource.Update()
    coneModelNodeToUpdate.SetAndObservePolyData(coneSource.GetOutput())

    if coneModelNodeToUpdate.GetDisplayNode() is None:
      displayNode = slicer.vtkMRMLModelDisplayNode()
      slicer.mrmlScene.AddNode(displayNode)
      displayNode.SetName('ConeModelDisplay')
      coneModelNodeToUpdate.SetAndObserveDisplayNodeID(displayNode.GetID())

    return coneModelNode

  def getConeTip(self, coneModelNode):
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

    return coneTip

  def getCenterOfConeBase(self, coneSource, coneModelNode):
    coneModelPolyData = coneModelNode.GetPolyData()
    numPointsInCone = coneModelPolyData.GetNumberOfPoints()
    conePointsTupleArray = []

    for point in range(numPointsInCone):
      conePointsTupleArray.append(coneModelPolyData.GetPoint(point))
    coneBasePoints = []

    for index in range(1, numPointsInCone):
      point = conePointsTupleArray[index]
      coneBasePoints.append(point)
    xSum, ySum, zSum = 0, 0, 0
    for (x,y,z) in coneBasePoints:
      xSum += x
      ySum += y
      zSum += z
    coneBaseCenter_x = xSum / coneSource.GetResolution()
    coneBaseCenter_y = ySum / coneSource.GetResolution()
    coneBaseCenter_z = zSum / coneSource.GetResolution()

    #Place fiducial at cone base
    markupsLogic = slicer.modules.markups.logic()
    markupsLogic.SetDefaultMarkupsDisplayNodeGlyphScale(5.0)
    markupsLogic.SetDefaultMarkupsDisplayNodeColor(0.0, 0.0, 0.0)
    markupsLogic.SetDefaultMarkupsDisplayNodeSelectedColor(0.0, 0.0, 0.0)
    markupsLogic.AddFiducial(coneBaseCenter_x, coneBaseCenter_y, coneBaseCenter_z)
    fidList = slicer.util.getNode('F')
    fidList.SetNthFiducialLabel(1, 'Cone Base Center')

  #
  # Set up and perform landmark registration
  #

  def computeThirdPointsForLandmarkRegistration(self, cameraPosition, coneTip):
    '''
    Create a point perpendicular to conetip-axis
    '''
    markupsLogic = slicer.modules.markups.logic()
    markupsLogic.SetDefaultMarkupsDisplayNodeGlyphScale(5.0)
    markupsLogic.SetDefaultMarkupsDisplayNodeColor(0.0, 0.0, 0.0)
    markupsLogic.SetDefaultMarkupsDisplayNodeSelectedColor(0.0, 0.0, 0.0)
    markupsLogic.AddNewFiducialNode()

    pointCoplanarToConeTip = (coneTip[0], coneTip[1] + 100 , coneTip[2]) #Add arbitrary distance along plane
    markupsLogic.AddFiducial(pointCoplanarToConeTip[0],pointCoplanarToConeTip[1],pointCoplanarToConeTip[2])
    midpointOfConeTipLine = ((coneTip[0] + pointCoplanarToConeTip[0])/2 , (coneTip[1] + pointCoplanarToConeTip[1])/2, (coneTip[2] + pointCoplanarToConeTip[2])/2)
    markupsLogic.AddFiducial(midpointOfConeTipLine[0],midpointOfConeTipLine[1],midpointOfConeTipLine[2])
    perpendicularPointCone = (midpointOfConeTipLine[0], midpointOfConeTipLine[1], midpointOfConeTipLine[2] + 100)
    markupsLogic.AddFiducial(perpendicularPointCone[0],perpendicularPointCone[1],perpendicularPointCone[2])
    '''
    Create a point perpendicular to camera-position axis, in the same way as above
    '''
    pointCoplanarToCameraPosition = (cameraPosition[0], cameraPosition[1] + 100 , cameraPosition[2]) #Add arbitrary distance along plane
    markupsLogic.AddFiducial(pointCoplanarToCameraPosition[0],pointCoplanarToCameraPosition[1],pointCoplanarToCameraPosition[2])
    midpointOfCameraPositionLine = ((cameraPosition[0] + pointCoplanarToCameraPosition[0])/2 , (cameraPosition[1] + pointCoplanarToCameraPosition[1])/2, (cameraPosition[2] + pointCoplanarToCameraPosition[2])/2)
    markupsLogic.AddFiducial(midpointOfCameraPositionLine[0],midpointOfCameraPositionLine[1],midpointOfCameraPositionLine[2])
    perpendicularPointRAS = (midpointOfCameraPositionLine[0], midpointOfCameraPositionLine[1], midpointOfCameraPositionLine[2] + 100)
    markupsLogic.AddFiducial(perpendicularPointRAS[0],perpendicularPointRAS[1],perpendicularPointRAS[2])
    print perpendicularPointRAS

    #Return third point pair as a named tuple
    FiducialPairThree = collections.namedtuple('FiducialPairThree', ['perpendicularPointCone', 'perpendicularPointRAS'])
    fidPairThree = FiducialPairThree(perpendicularPointCone, perpendicularPointRAS)
    return fidPairThree

  def performLandmarkRegistion(self, fromFiducialsNode, toFiducialsNode, outputTransformNode):
    # Initialize fiducial registration wizard node
    fiducialRegistrationWizardNode = slicer.vtkMRMLFiducialRegistrationWizardNode()
    slicer.mrmlScene.AddNode(fiducialRegistrationWizardNode)
    fiducialRegistrationLogic = slicer.modules.fiducialregistrationwizard.logic()
    fiducialRegistrationWizardNode.SetRegistrationModeToRigid()
    fiducialRegistrationWizardNode.SetAndObserveFromFiducialListNodeId(fromFiducialsNode.GetID())
    fiducialRegistrationWizardNode.SetAndObserveToFiducialListNodeId(toFiducialsNode.GetID())
    fiducialRegistrationWizardNode.SetOutputTransformNodeId(outputTransformNode.GetID())

    # Add fiducials where ...
    #   Fiducial pair 1 -- Cone tip & camera position
    #   Fiducial pair 2 -- Center of cone base & target model center of mass (COM)
    #   Fiducial pair 3 -- Perpendicular points to tip-camera axis and base-modelCOM axis
    fiducialRegistrationLogic.AddFiducial(fromFiducialsNode.GetNthFiducial(0), toFiducialsNode.GetNthFiducial(0))
    fiducialRegistrationLogic.AddFiducial(fromFiducialsNode.GetNthFiducial(1), toFiducialsNode.GetNthFiducial(1))
    fiducialRegistrationLogic.AddFiducial(fromFiducialsNode.GetNthFiducial(2), toFiducialsNode.GetNthFiducial(2))

    # Update calibration
    fiducialRegistrationLogic.UpdateCalibration(fiducialRegistrationWizardNode)

    return outputTransformNode

  #
  # Set up and perform collision detection
  #

  def setUpCollisionDetection(self,coneModel, movingModel,coneModelToRAS,movingModelToRAS):
    #Set up VTK collision detection from Slicer RT
    #Note:  Models are assumed to not be nested underneath each other in the transform hierarchy
    from vtkSlicerRtCommonPython import vtkCollisionDetectionFilter
    self.coneMovingModelCollisionDetection = vtkCollisionDetectionFilter()
    self.coneMovingModelCollisionDetection.SetInput(0, coneModel.GetPolyData())
    self.coneMovingModelCollisionDetection.SetInput(1, movingModel.GetPolyData())
    self.coneMovingModelCollisionDetection.SetMatrix(0, coneModelToRAS)
    self.coneMovingModelCollisionDetection.SetMatrix(1, movingModelToRAS)
    self.coneMovingModelCollisionDetection.Update()
    return self.coneMovingModelCollisionDetection

  def onCameraPositionChanged(self):
    #TODO: Figure out how to adaptively redraw cone
    self.checkForCollisions()

  def onMovingModelPositionChanged(self):
    self.checkForCollisions()

  def checkForCollisions(self):
    self.coneMovingModelCollisionDetection.Update()
    text = " "
    if self.coneMovingModelCollisionDetection.GetNumberOfContacts() > 0:
      text = text + "Collision detected between moving model and cone bounding target model!"

    if len(text) > 0:
      self.collisionWarningLabel.setText(text)
      self.collisionWarningLabel.setStyleSheet('color: red')
    elif len(text) == 0:
      self.collisionWarningLabel.setText("No collisions detected!")
      self.collisionWarningLabel.setStyleSheet('color: green')

#-------------------------------------------------------------------------------
#
# AutoTransparencyTest
#
#-------------------------------------------------------------------------------
class AutoTransparencyTest(ScriptedLoadableModuleTest):
  def setUp(self):
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_NoCollisions()
    #if true:
      #slicer.mrmlScene.Clear(0)
    #self.test_Collisions()
    #if true:
      #slicer.mrmlScene.Clear(0)

  def createSampleModels_NoCollisions(self):
    #Create a cautery model
    moduleDirectoryPath = slicer.modules.autotransparency.path.replace('AutoTransparency.py', '')
    slicer.util.loadModel(qt.QDir.toNativeSeparators(moduleDirectoryPath + 'Resources/CAD/Cautery.stl'))
    self.cauteryModelNode = slicer.util.getNode(pattern = "Cautery")
    self.cauteryModelNode.GetDisplayNode().SetColor(1.0, 1.0, 0)
    self.cauteryModelNode.SetName("CauteryModel")
    self.cauteryModelNode.GetDisplayNode().SliceIntersectionVisibilityOn()

    #Create transform node and set transform of transform node
    self.cauteryModelToRAS = slicer.vtkMRMLLinearTransformNode()
    self.cauteryModelToRAS.SetName('CauteryModelToRAS')
    slicer.mrmlScene.AddNode(self.cauteryModelToRAS)
    cauteryModelToRASTransform = vtk.vtkTransform()
    cauteryModelToRASTransform.PreMultiply()
    cauteryModelToRASTransform.Translate(0, 100, 0)
    cauteryModelToRASTransform.RotateX(30)
    cauteryModelToRASTransform.Update()
    self.cauteryModelToRAS.SetAndObserveTransformToParent(cauteryModelToRASTransform)

    #Transform the cautery model
    self.cauteryModelNode.SetAndObserveTransformNodeID(self.cauteryModelToRAS.GetID())

    #Create a sphere tumor model
    self.tumorModelNode = slicer.modules.createmodels.logic().CreateSphere(10)
    self.tumorModelNode.GetDisplayNode().SetColor(0,1,0) #Green
    self.tumorModelNode.SetName('TumorModel')

    #Create transform node and set transform of transform node
    self.tumorModelToRAS = slicer.vtkMRMLLinearTransformNode()
    self.tumorModelToRAS.SetName('tumorModelToRAS')
    slicer.mrmlScene.AddNode(self.tumorModelToRAS)
    tumorModelToRASTransform = vtk.vtkTransform()
    self.tumorModelToRAS.SetAndObserveTransformToParent(tumorModelToRASTransform)

    #Transform the tumor model
    self.tumorModelNode.SetAndObserveTransformNodeID(self.tumorModelToRAS.GetID())

  def test_NoCollisions(self):
    self.delayDisplay("Starting the test")
    # Create models of needle and cautery, in a position that does not represent
    # collision
    self.createSampleModels_NoCollisions()

    # Compute the center of mass of the target model node
    tumorModelNode = slicer.mrmlScene.GetNodeByID('vtkMRMLModelNode5')
    tumorModelPolyData = tumorModelNode.GetPolyData()
    testingLogic = AutoTransparencyLogic()
    centerFilter = testingLogic.computeCenterOfMass(tumorModelPolyData)

    # Transform center to RAS coordinate system
    center = []
    for i,val in enumerate(centerFilter.GetCenter()):
      center.append(val)

    center.append(1.0)
    tumorModelToRAS_transformNode = slicer.mrmlScene.GetNodeByID('vtkMRMLLinearTransformNode5')
    tumorModelToRAS_vtkMatrix = vtk.vtkMatrix4x4()
    tumorModelToRAS_transformNode.GetMatrixTransformToParent(tumorModelToRAS_vtkMatrix)
    tumorModelToRAS_vtkMatrix.MultiplyPoint(center,center)
    center.remove(1.0)
    print "Center of mass in RAS: ", center

    # Get the camera node's position
    cameraPosition = testingLogic.getCameraPosition()
    print "Camera position: ", cameraPosition

    # Find cone dimensions
    coneDimensions = testingLogic.computeConeDimensions(tumorModelPolyData, center, cameraPosition)

    # Create a model of the cone and visualize it in the scene
    resolution = 10
    coneSource = testingLogic.createConeSource(coneDimensions, center, resolution)
    coneModelNode = testingLogic.drawCone(coneSource, coneDimensions, center)

    # Find the tip of cone and the center of the base of the cone, points which
    # will be used as inputs for the landmark registration
    coneTip = testingLogic.getConeTip(coneModelNode)

    # Compute center of mass of points of cone base
    coneBaseCenter = testingLogic.getCenterOfConeBase(coneSource, coneModelNode)

    # Create a third point for use in landmark registration, perpendicular to a
    # line drawn in the AP plane of the cone tip
    pointPairThree = testingLogic.computeThirdPointsForLandmarkRegistration(cameraPosition, coneTip)

    #TODO: Compute landmark registration to get coneModelToRAS transform
    coneModelFiducialsNode = slicer.vtkMRMLFiducialListNode()
    coneModelFiducialsNode.AddFiducialWithLabelXYZSelectedVisibility('coneTip', \
                                                                      coneTip[0], \
                                                                      coneTip[1], \
                                                                      coneTip[2], \
                                                                      0, \
                                                                      0)
    coneModelFiducialsNode.AddFiducialWithLabelXYZSelectedVisibility('centerConeBase', \
                                                                      coneBaseCenter[0], \
                                                                      coneBaseCenter[1], \
                                                                      coneBaseCenter[2], \
                                                                      0, \
                                                                      0)
    coneModelFiducialsNode.AddFiducialWithLabelXYZSelectedVisibility('perpendicularPointConeAxis', \
                                                                      pointPairThree.perpendicularPointCone[0], \
                                                                      pointPairThree.perpendicularPointCone[1], \
                                                                      pointPairThree.perpendicularPointCone[2], \
                                                                      0, \
                                                                      0)

    rasFiducialsNode = slicer.vtkMRMLFiducialListNode()
    rasFiducialsNode.AddFiducialWithLabelXYZSelectedVisibility('cameraPosition', \
                                                                cameraPosition[0], \
                                                                cameraPosition[1], \
                                                                cameraPosition[2], \
                                                                0, \
                                                                0)
    rasFiducialsNode.AddFiducialWithLabelXYZSelectedVisibility('modelCOM', \
                                                                center[0], \
                                                                center[1], \
                                                                center[2], \
                                                                0, \
                                                                0)
    rasFiducialsNode.AddFiducialWithLabelXYZSelectedVisibility('perpendicularPointRAS', \
                                                                pointPairThree.perpendicularPointRAS[0], \
                                                                pointPairThree.perpendicularPointRAS[1], \
                                                                pointPairThree.perpendicularPointRAS[2], \
                                                                0, \
                                                                0)
    coneModelToRAS = testingLogic.performLandmarkRegistion(coneModelFiducialsNode, rasFiducialsNode, coneModelToRAS)

    #TODO: Check if collision is occcuring
    coneCauteryCollisionDetectionFilter = \
    testingLogic.setUpCollisionDetection(coneModelNode, tumorModelNode, coneModelToRAS, movingModelToRAS)

    self.delayDisplay('Non-collision test passed!')
