bl_info = {
    "name": "Rigify To Animaze",
    "author": "Dukhart",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Object > Apply > Rigify to Animaze, TopBar > File > Export > Animaze",
    "description": "Converts Rigify Rig to be compatible with Animaze",
    "warning": "Still inDevelopment!!! plugin independently developed by the techArtist Dukhart",
    "doc_url": "www.Dukhart.ca/BlenderAnimazePlugin","www.GitHub.com/Dukhart/BlenderAnimazePlugin"
    "category": "Apply",
}

import bpy
import os
import math
       
class RIGIFY_TO_ANIMAZE_OT_convert_rig(bpy.types.Operator):
    """Converts Rigify rig to Animaze"""
    bl_idname = "rigify_to_animaze.convert_rig"
    bl_label = "Rigify to Animaze"

    def execute(self, context):
        obj = context.active_object
        exit_code = {'FINISHED'}
        if not obj.type == 'ARMATURE':
            self.report({'ERROR'},'No armature selected')
            exit_code = {'CANCELLED'}
            return exit_code
        
        exit_code = self.convertBoneNames(self, obj)
        exit_code = self.fixMandatoryNames(self, obj)
        exit_code = self.addCameraBone(self, obj)
        
        self.report({'INFO'},'Conversion finished: ' + str(exit_code))
        
        return exit_code
        
    @classmethod
    def renameActionDataPath(context, path, oldName, newName):
        pathParse  = path.split('"')
        preffix = pathParse[0]
        pathName = pathParse[1]
        suffix = pathParse[2]
        
        if pathName == oldName:
            newPath = preffix + '"' + newName + '"' + suffix
            return newPath
        else:
            return path
        
    @classmethod
    def renameBone_ActionUpdate(context, armObj, self, bone, newName):
        self.updateActions(armObj, self, bone.name, newName)
        bone.name = newName
        
    @classmethod
    def updateActions (context, obj, self, oldName, newName):
        self.report({'INFO'}, 'OLD= ' + oldName)
        self.report({'INFO'}, 'NEW= ' + newName)
        if not obj.type == 'ARMATURE':
            self.report({'ERROR'}, 'No armature selected')
            return {'CANCELLED'}
        
        actions = bpy.data.actions
        for action in actions:
            print('Updating... ' + oldName + ' to ' + newName + ' on action: ' + action.name)
            if action:
                for fcurve in action.fcurves:
                    #print('fcurvename: ' + fcurve.data_path + ' group: ' + fcurve.group.name)
                    if fcurve.group.name == oldName:
                        fcurve.group.name = newName
                    
                    fcurve.data_path = self.renameActionDataPath(fcurve.data_path, oldName, newName)
    @classmethod
    def convertBoneNames(context, self, obj):
        arma = obj.data
        for bone in arma.bones:
            name = self.convertBoneName(bone.name)
            self.renameBone_ActionUpdate(obj, self, bone, name)
        return {'FINISHED'}
            
    #convert Bone Names
    @classmethod
    def convertBoneName(context, inName):
        namePrefix = "Bip"
        nameSuffix = ""
        #Capitalize the First Letter
        name = inName[0].upper()
        if (len(inName) > 1):
            name += inName[1 : len(inName)]
        
        #remove numbers and store in suffix
        if inName[len(inName)-1].isnumeric():
            nameSuf = name[len(name)-3:len(name)]
            name = name[0:len(name)-4]
            
            j = 0
            for a in nameSuf:
                if a != '0':
                    break
                j += 1
                
            nameSuffix = nameSuf[j:len(nameSuf)]
        
        #Move left right to prefix
        if name[len(name) - 1] == 'L' or name[len(name) - 1] == 'R':
            namePrefix += name[len(name) - 1]
            name = name[0:len(name)-2]
        #Move bottom top to prefix
        if name[len(name) - 1] == 'B' or name[len(name) - 1] == 'T':
            namePrefix += name[len(name) - 1]
            name = name[0:len(name)-2]
        name = namePrefix + name + nameSuffix
        return name
    
    @classmethod
    def fixMandatoryNames(context, self, obj):
        self.report({'INFO'}, 'Applying Mandantory names to appropriate bones')
        arma = obj.data
        # EyeBones
        self.renameMandatoryBone(self,'BipLEye','BipLParentEye')
        self.renameMandatoryBone(self,'BipREye','BipRParentEye')
        self.renameMandatoryBone(self,'BipLMCH-eye','BipLEye')
        self.renameMandatoryBone(self,'BipRMCH-eye','BipREye')
        
        #head bone
        self.renameMandatoryBone(self,'BipHead', 'BipMCHHead')
        self.renameMandatoryBone(self,'BipDEF-head', 'BipHead')
        return {'FINISHED'}
            
    @classmethod
    def renameMandatoryBone(context, self, boneName, newName):
        if not bpy.context.object:
            return
        obj = bpy.context.object
        b = obj.data.bones.find(boneName)
        if b >= 0:
            bone = obj.data.bones[b]
            #bone.name = 'BipREye'
            self.report({'INFO'}, 'renaming  ' + boneName)
            self.renameBone_ActionUpdate(obj, self, bone, newName)
            
    @classmethod
    def addCameraBone(context, self, obj):
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bone = obj.data.edit_bones.new('Camera')
        
        zOff = 0.5
        height = 0.1
        distance = -4.0
        
        bone.head = (0.0, distance, 0.0 + zOff)
        bone.tail = (0.0, distance, height + zOff)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        return {'FINISHED'}
    
class RIGIFY_TO_ANIMAZE_OT_export_fbx(bpy.types.Operator):
    """Exports fbx files needed for Animaze"""
    bl_idname = "rigify_to_animaze.export_fbx"
    bl_label = "Animaze"
    
    blendName = bpy.path.basename(bpy.context.blend_data.filepath)
    #print(blendName)
    avatarName = 'none'
    
    def execute(self, context):
        self.avatarName = self.trimString(self.blendName,6)
        print(self.avatarName)
        path = bpy.path.abspath('//')
        subFolder = 'Animaze'
        dir = path + subFolder
        #path = dir + "\\" + self.avatarName + ".fbx"
        if os.path.isdir(dir) == False:
            self.report({'WARNING'}, 'Directory not found. making dir ' + dir)
            os.makedirs(dir)
        
        self.exportMeshArmature(self, dir)
        
        dir += '\\Animation'
        if os.path.isdir(dir) == False:
            self.report({'WARNING'}, 'Directory not found. making dir ' + dir)
            os.makedirs(dir)
        
        self.exportAnimation(dir + "\\")
        self.report({'INFO'}, 'Export ' + self.avatarName + ' complete')
        return {'FINISHED'}
    
    #trims i number of chars from the end of s
    @classmethod
    def trimString(context, s, i):
        print('i: ' + str(i) + ' s: ' + s)
        return s[0:len(s)-i]
    
    #exports mesh and armature for use with animaze
    @classmethod
    def exportMeshArmature(context, self, dir):
        anim_data = bpy.context.object.animation_data
        i = bpy.data.actions.find('idle1')
        action = bpy.data.actions[i]
        anim_data.action = action
        
        objType = {'MESH', 'ARMATURE'}
        path = dir + "\\" + self.avatarName + ".fbx"
        
        bpy.ops.export_scene.fbx(
        filepath=path, check_existing=True, filter_glob='*.fbx', 
        use_selection=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, 
        apply_scale_options='FBX_SCALE_UNITS', bake_space_transform=True, object_types=objType, 
        use_mesh_modifiers=False, use_mesh_modifiers_render=False, mesh_smooth_type='OFF', 
        use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_custom_props=False, 
        add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=True,
        armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, 
        bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, 
        bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=True, batch_mode='OFF', 
        use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y'
        )
    
    # exports all actions on the armature
    # TODO limit to only actions relevent -> nla track list
    @classmethod
    def exportAnimation(context, dir):
        anim_data = bpy.context.object.animation_data
        #we only want the armature for the animations
        objType = {'ARMATURE'}
        for action in bpy.data.actions:
            path = dir + "\\"  + action.name + ".fbx"
            anim_data.action = action
            
            bpy.ops.export_scene.fbx(
            filepath=path, check_existing=True, filter_glob='*.fbx', 
            use_selection=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, 
            apply_scale_options='FBX_SCALE_UNITS', bake_space_transform=True, object_types=objType, 
            use_mesh_modifiers=False, use_mesh_modifiers_render=False, mesh_smooth_type='OFF', 
            use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_custom_props=False, 
            add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=True,
            armature_nodetype='NULL', bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, 
            bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, 
            bake_anim_simplify_factor=0.1, path_mode='AUTO', embed_textures=False, batch_mode='OFF', 
            use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y'
            )

def draw_item_fbx(self, context):
    layout = self.layout
    layout.operator("rigify_to_animaze.export_fbx")
    
def draw_item_rig(self, context):
    layout = self.layout
    layout.operator("rigify_to_animaze.convert_rig")

def register():
    bpy.utils.register_class(RIGIFY_TO_ANIMAZE_OT_convert_rig)
    bpy.utils.register_class(RIGIFY_TO_ANIMAZE_OT_export_fbx)
    
    bpy.types.TOPBAR_MT_file_export.append(draw_item_fbx)
    bpy.types.VIEW3D_MT_object_apply.append(draw_item_rig)
    
def unregister():
    bpy.utils.unregister_class(RIGIFY_TO_ANIMAZE_OT_convert_rig)
    bpy.utils.unregister_class(RIGIFY_TO_ANIMAZE_OT_export_fbx)
    
    bpy.types.TOPBAR_MT_file_export.remove(draw_item_fbx)
    bpy.types.VIEW3D_MT_object_apply.remove(draw_item_rig)

if __name__ == "__main__":
    register()

    # test call
    #bpy.ops.rigify_to_animaze.convert_rig()
    #bpy.ops.rigify_to_animaze.export_fbx()