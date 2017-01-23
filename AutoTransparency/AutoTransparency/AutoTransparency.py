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
    # input target model selector
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
    # input moving model selector
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
    # check box to enable autotransparency throughout Slicer
    #
    self.enableAutoTransparencyFlagCheckBox = qt.QCheckBox()
    self.enableAutoTransparencyFlagCheckBox.checked = 0
    self.enableAutoTransparencyFlagCheckBox.setToolTip("If checked, enable AutoTransparency.")
    parametersFormLayout.addRow("Enable AutoTransparency", self.enableAutoTransparencyFlagCheckBox)

    # connections
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

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
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = AutoTransparencyLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
