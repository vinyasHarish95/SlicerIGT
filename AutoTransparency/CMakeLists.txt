cmake_minimum_required(VERSION 2.8.9)

project(AutoTransparency)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/AutoTransparency")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Vinyas Harish (Perk Lab (Queen's University)), Tamas Ungi (Perk Lab (Queen's University))")
set(EXTENSION_DESCRIPTION "Prevent the occlusion of a target model, even when other models are present by adaptively changing their transparency.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/AutoTransparency.png")
#Icons made by <a href="http://www.freepik.com" title="Freepik">Freepik</a> from <a #href="http://www.flaticon.com" title="Flaticon">www.flaticon.com</a> is licensed by <a #href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" #target="_blank">CC 3.0 BY</a></div>
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/AutoTransparency/Screenshots/1.png") 
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(AutoTransparency)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
