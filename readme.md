# **Pixel Perfect**
## **About**
Pixel Perfect is an Blender add-on to simplify the creation of Low Poly Pixel Art with three small but time saving features. 

1. Isolate By direction
2. Unwrap Pixel Perfect UVs
3. Modify UVs designed for pixelart
4. Export a UV Layout texture with sharp unique colored UV boarders.

## **How to use**
### 1. Isolate by Direction
After selecting faces in edit mode the command can be executed by opening the context menu under **Isolate by Direction** -> ***Direction***. Every face wich angle between its normal and the defined direction is smaller then the4 max angle is isolated.

### 2. Unwrap Pixel Perfect  UVs
First select an image in the **UV Image Editor**. Then in **Edit-mode** open the **UV Mapping** options by pressing **U** in the **3D View**. Select **Unwrap Pixel Perfect by Direction** or **Unwrap Pixel Perfect by Size**. The UVs of every selected face gets recalculated. Note: 1 Unit equals 1 Pixel. So in order to set up your Pixel density change the **Units** in the **Scene** tab.

- **Unwrap Pixel Perfect by X, Y, Z, Custom, Auto**:  
  Projects a selected face to the selected plain or in case of Auto to the closest plain and converts to UVs. Good, when the face normal closely directs towards the major orientations X, Y, Z. 
- **Unwrap Pixel Perfect by Normal**:  
  Projects a selected face to the normal plain and converts to UVs. Good, when the face is strongly rotated. E.g. 45° around Z.

### 3. Modify UVs
- **Group to Pixel**:  
  Hover over a Vertex and run this command under **UV Context Menu** -> **Snap** -> **Group to Pixel** as Shortcut. The hovered vertex moves to the closest pixel corner. Every selected vertex is moved respectively.
- **Group to orthogonal Line**:  
  Hover over a edge and run this command under **UV Context Menu** -> **Snap** -> **Group to orthogonal Line** as Shortcut. The closest angle between the edge and either the x ore the y axises is calculated. Every connected vertex is rotated around to the mouse closest vertex by this angel.

### 4. Export UV Layout
While still in **Edit-mode** select all Faces and click on the **UV** header bar option of the **UV Editor**. Select **Export Pixel UV Layout** and save the image on your system.

## **Installation**
To install this add-on just click the **Code** button and then **Download ZIP**. Save anywhere on your computer and open Blender. 
In Blender under **Edit** -> **Preferences...** -> **Add-ons** click the **Install...** button and select the downloaded file. Now enter the name **Pixel Perfect** in the search bar and activate the add-one. Your done!

## **Tipps**
- Set **Pixel Coordinates** inside the **UV Editor** -> **View** panel to `True` for an easier workflow.