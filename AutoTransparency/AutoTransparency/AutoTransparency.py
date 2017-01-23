import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

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
    self.parent.contributors = ["Vinyas Harish, Tamas Ungi (PerkLab, Queen's)"]
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
    self.test_AutoTransparency1()

  def test_AutoTransparency1(self):
    self.delayDisplay("Starting the test")

    #Create a needle model
    needleModelNode = slicer.modules.createmodels.logic().CreateNeedle(80,3.0,7,0)

    #Create transform node and set transform of transform node
    needleModelToRas = slicer.vtkMRMLLinearTransformNode()
    needleModelToRas.SetName('NeedleModelToRas')
    slicer.mrmlScene.AddNode(needleModelToRas)
    needleModelToRasTransform = vtk.vtkTransform()
    needleModelToRasTransform.PreMultiply()
    needleModelToRasTransform.Translate(0, 100, 0)
    needleModelToRasTransform.RotateX(30)
    needleModelToRasTransform.Update()
    needleModelToRas.SetAndObserveTransformToParent(needleModelToRasTransform)

    #Transform the needle model
    needleModelNode.SetAndObserveTransformNodeID(needleModelToRas.GetID())

    #Create a sphere tumor model
    tumorModelNode = slicer.modules.createmodels.logic().CreateSphere(10)
    tumorModelNode.GetDisplayNode().SetColor(0,1,0) #Green

    #Create transform node and set transform of transform node
    tumorModelToRas = slicer.vtkMRMLLinearTransformNode()
    tumorModelToRas.SetName('tumorModelToRas')
    slicer.mrmlScene.AddNode(tumorModelToRas)
    tumorModelToRasTransform = vtk.vtkTransform()
    tumorModelToRas.SetAndObserveTransformToParent(tumorModelToRasTransform)

    #Transform the tumor model
    tumorModelNode.SetAndObserveTransformNodeID(tumorModelToRas.GetID())
    self.delayDisplay('Test passed!')
