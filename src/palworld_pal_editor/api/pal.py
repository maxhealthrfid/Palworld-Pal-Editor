import copy
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import traceback
import json
from typing import Optional
import tempfile
import os
import time

from palworld_pal_editor.utils.util import reply

from palworld_pal_editor.core import SaveManager, PalEntity, PlayerEntity
from palworld_pal_editor.utils import LOGGER
from palworld_save_tools.json_tools import CustomEncoder

pal_blueprint = Blueprint("pal", __name__)

# 用于存储临时转移数据的字典
_temp_transfer_data = {}


# Update Pal Data
@pal_blueprint.route("/paldata", methods=["PATCH"])
@jwt_required()
def patch_paldata():
    PalGuid = request.json.get("PalGuid")
    PlayerUId = request.json.get("PlayerUId")
    key = request.json.get("key")
    value = request.json.get("value")
    if PlayerUId == "PAL_BASE_WORKER_BTN":
        pal_entity = SaveManager().get_working_pal(PalGuid)
    else:
        pal_entity = SaveManager().get_player(PlayerUId).get_pal(PalGuid)
    try:
        match key:
            case "HasWorkerSick":
                pal_entity.heal_pal()
            case "IsFaintedPal":
                pal_entity.heal_pal()
            case "set_Suitability":
                pal_entity.set_WorkSuitability(value.get("name"), value.get("level"))
            case "pop_PassiveSkillList":
                pal_entity.pop_PassiveSkillList(item=value)
            case "pop_MasteredWaza":
                pal_entity.pop_MasteredWaza(item=value)
            case "pop_EquipWaza":
                pal_entity.pop_EquipWaza(item=value)
            case "add_PassiveSkillList":
                if not pal_entity.add_PassiveSkillList(value, True):
                    return reply(
                        1,
                        None,
                        f"Too many skills, or skill {value} already exists! Or we can't find it in database.",
                    )
            case "add_MasteredWaza":
                if not pal_entity.add_MasteredWaza(value):
                    return reply(
                        1,
                        None,
                        f"Too many skills, or skill {value} already exists! Or we can't find it in database.",
                    )
            case "add_EquipWaza":
                if not pal_entity.add_EquipWaza(value, True):
                    return reply(
                        1,
                        None,
                        f"Too many skills, or skill {value} already exists! Or we can't find it in database.",
                    )
            case "in_owner_palbox":
                if PlayerUId == "PAL_BASE_WORKER_BTN":
                    return reply(1, None, f"Moving pal to basecamp is unsupported.")
                player = SaveManager().get_player(PlayerUId)
                if not SaveManager().move_pal(
                    pal_entity.InstanceId,
                    [player.OtomoCharacterContainerId, player.PalStorageContainerId],
                ):
                    return reply(1, None, f"No enough slot in pal container.")
            case "heal_all_pals":
                SaveManager().heal_all_pals()
            case _:
                if isinstance(err := setattr(pal_entity, key, value), TypeError):
                    return reply(1, None, f"Error in patch_paldata {err}")
    except Exception as e:
        stack_trace = traceback.format_exc()
        LOGGER.error(f"Error in patch_paldata {stack_trace}")
        return reply(1, None, f"Error in patch_paldata {stack_trace}")
    return reply(0)


# Get Pal Data
@pal_blueprint.route("/paldata", methods=["POST"])
@jwt_required()
def paldata():
    InstanceId = request.json.get("InstanceId")
    PlayerUId = request.json.get("PlayerUId")
    if PlayerUId == "PAL_BASE_WORKER_BTN":
        pal = SaveManager().get_working_pal(InstanceId)
        LOGGER.info(f"Get BASE WORKER {pal}")
    else:
        try:
            player = SaveManager().get_player(PlayerUId)
            pal = player.get_pal(InstanceId)
            LOGGER.info(f"Get {player.NickName}'s pal: {pal}")
        except:
            pass
    if pal:
        return reply(
            0,
            _pal_data(pal),
        )
    LOGGER.warning(
        f"Failed Getting Pal with PlayerID: {PlayerUId}, PalID: {InstanceId}"
    )
    return reply(
        1, None, f"Failed Getting Pal with PlayerID: {PlayerUId}, PalID: {InstanceId}"
    )


# Just some dumb shit
def _pal_data(pal: PalEntity):
    return {
        "InstanceId": str(pal.InstanceId) if pal.InstanceId else None,
        "OwnerPlayerUId": (str(pal.OwnerPlayerUId) if pal.OwnerPlayerUId else None),
        "group_id": str(pal.group_id) if pal.group_id else None,
        "ContainerId": str(pal.ContainerId) if pal.CharacterID else None,
        "SlotIndex": pal.SlotIndex,
        "OwnerName": pal.OwnerName or None,
        "CharacterID": pal.CharacterID,
        "IconAccessKey": pal.IconAccessKey or None,
        "DataAccessKey": pal.DataAccessKey or None,
        "I18nName": pal.I18nName or None,
        "DisplayName": pal.DisplayName or None,
        "NickName": pal.NickName or "",
        "Gender": pal.Gender.value if pal.Gender else None,
        "Level": pal.Level or 1,
        "HasTowerVariant": pal.HasTowerVariant,
        "HasWorkerSick": pal.HasWorkerSick,
        "IsFaintedPal": pal.IsFaintedPal,
        "Is_Unref_Pal": pal.is_unreferenced_pal,
        "in_owner_palbox": pal.in_owner_palbox,
        "IsPal": pal.IsPal,
        "IsHuman": pal.IsHuman,
        "IsBOSS": pal.IsBOSS or False,
        "IsRarePal": pal.IsRarePal or False,
        "IsTower": pal.IsTower or False,
        "IsRAID": pal.IsRAID or False,
        "IsPREDATOR": pal.IsPREDATOR or False,
        "IsOilrig": pal.IsOilrig or False,
        "IsExpeditionPal": pal.IsExpeditionPal,
        "ComputedMaxHP": pal.ComputedMaxHP or None,
        "ComputedAttack": pal.ComputedAttack or None,
        "ComputedDefense": pal.ComputedDefense or None,
        "ComputedCraftSpeed": pal.ComputedCraftSpeed or None,
        "Rank": pal.Rank if pal.Rank else 1,
        "Rank_HP": pal.Rank_HP or 0,
        "Rank_Attack": pal.Rank_Attack or 0,
        "Rank_Defence": pal.Rank_Defence or 0,
        "Rank_CraftSpeed": pal.Rank_CraftSpeed or 0,
        "Talent_HP": pal.Talent_HP or 0,
        "Talent_Melee": pal.Talent_Melee or 0,
        "Talent_Shot": pal.Talent_Shot or 0,
        "Talent_Defense": pal.Talent_Defense or 0,
        "PassiveSkillList": pal.PassiveSkillList or [],
        "EquipWaza": pal.EquipWaza or [],
        "MasteredWaza": pal.MasteredWaza or [],
        "Suitabilities": pal.WorkSuitabilities or {},
    }


@pal_blueprint.route("/dump_data", methods=["POST"])
@jwt_required()
def dump_data():
    PalGuid = request.json.get("PalGuid")
    PlayerUId = request.json.get("PlayerUId")
    if PlayerUId == "PAL_BASE_WORKER_BTN":
        pal = SaveManager().get_working_pal(PalGuid)
        LOGGER.info(f"Get BASE WORKER {pal}")
    else:
        try:
            player = SaveManager().get_player(PlayerUId)
            pal = player.get_pal(PalGuid)
            LOGGER.info(f"Get {player.NickName}'s pal: {pal}")
        except:
            pass
    if pal:
        return reply(0, pal.dump_obj())
    LOGGER.warning(f"Failed Getting Pal with PlayerID: {PlayerUId}, PalID: {PalGuid}")
    return reply(
        1, None, f"Failed Getting Pal with PlayerID: {PlayerUId}, PalID: {PalGuid}"
    )


@pal_blueprint.route("/pal/<pal_id>", methods=["DELETE"])
@jwt_required()
def delete_pal(pal_id):
    if SaveManager().delete_pal(pal_id):
        return reply(0)
    return reply(1, None, f"Error Deleting Pal {pal_id}, check logs for more info.")


@pal_blueprint.route("/add_pal", methods=["POST"])
@jwt_required()
def add_pal():
    PlayerUId = request.json.get("PlayerUId")
    if PlayerUId == "PAL_BASE_WORKER_BTN":
        LOGGER.warning("Directly add pal to basecamp is not yet supported.")
        return reply(1, None, f"Directly adding pal to basecamp is not yet supported.")
    else:
        try:
            pal_entity = SaveManager().add_pal(PlayerUId)
            if not pal_entity:
                return reply(
                    1,
                    None,
                    f"Failed adding pal, likely your pal containers are full, check logs for detail.",
                )
        except:
            return reply(
                1,
                None,
                f"Error happened during adding pal, check logs for detail. {traceback.format_exc()}",
            )
    return reply(0, _pal_data(pal_entity))


@pal_blueprint.route("/dupe_pal", methods=["POST"])
@jwt_required()
def dupe_pal():
    PalGuid = request.json.get("PalGuid")
    PlayerUId = request.json.get("PlayerUId")
    if PlayerUId == "PAL_BASE_WORKER_BTN":
        LOGGER.warning("Directly add pal to basecamp is not yet supported.")
        return reply(1, None, f"Directly adding pal to basecamp is not yet supported.")
    else:
        try:
            player = SaveManager().get_player(PlayerUId)
            pal_obj = player.get_pal(PalGuid)._pal_obj

            pal_entity = SaveManager().add_pal(PlayerUId, pal_obj)
            if not pal_entity:
                return reply(
                    1,
                    None,
                    f"Failed duping pal, likely your pal containers are full, check logs for detail.",
                )
        except:
            return reply(
                1,
                None,
                f"Error happened during duping pal, check logs for detail. {traceback.format_exc()}",
            )
    return reply(0, _pal_data(pal_entity))


@pal_blueprint.route("/source_pals", methods=["POST"])
@jwt_required()
def source_pals():
    source_save = request.json.get("source_save")
    
    if not source_save:
        return reply(1, None, "Missing source_save parameter")
    
    # 保存当前存档路径
    current_save = None
    try:
        LOGGER.info("\n=== Loading Source Save for Pal Selection ===")
        LOGGER.info(f"Opening source save: {source_save}")
        
        # 获取当前存档的所有信息，用于后续恢复
        current_manager = SaveManager()
        current_save = current_manager._file_path  # 使用正确的属性名
        LOGGER.info(f"\nCurrent save path: {current_save}")
        
        current_players = []
        for player in current_manager.get_players():
            current_players.append({
                'name': player.NickName,
                'uid': str(player.PlayerUId)
            })
        LOGGER.info("\nCurrent save players:")
        for player in current_players:
            LOGGER.info(f"  Player: {player['name']} - {player['uid']}")
        
        # 打开源存档
        LOGGER.info("\nOpening source save...")
        current_manager.open(source_save)
        
        # 获取源存档信息
        source_players = current_manager.get_players()
        LOGGER.info("\nSource save players:")
        for player in source_players:
            LOGGER.info(f"  Player: {player.NickName}")
            LOGGER.info(f"    - Player UID: {player.PlayerUId}")
            LOGGER.info(f"    - Pal count: {len(player.get_pals())}")
            LOGGER.info(f"    - Container IDs: {player.PalStorageContainerId}, {player.OtomoCharacterContainerId}")
        
        # 获取所有玩家的所有宠物
        all_pals = []
        for player in source_players:
            for pal in player.get_pals():
                LOGGER.info(f"\nFound pal in source save:")
                LOGGER.info(f"  - Display Name: {pal.DisplayName}")
                LOGGER.info(f"  - Character ID: {pal.CharacterID}")
                LOGGER.info(f"  - Instance ID: {pal.InstanceId}")
                LOGGER.info(f"  - Owner: {player.NickName} ({player.PlayerUId})")
                LOGGER.info(f"  - Container ID: {pal.ContainerId}")
                LOGGER.info(f"  - Slot Index: {pal.SlotIndex}")
                all_pals.append(_pal_data(pal))
                
        LOGGER.info(f"\nTotal pals found in source save: {len(all_pals)}")
        
        # 重新打开原存档
        LOGGER.info(f"\nReopening original save: {current_save}")
        current_manager.open(current_save)
        
        # 验证原存档是否正确恢复
        restored_players = current_manager.get_players()
        LOGGER.info("\nVerifying restored save:")
        for player in restored_players:
            LOGGER.info(f"  Player: {player.NickName} - {player.PlayerUId}")
        
        return reply(0, all_pals)
            
    except Exception as e:
        LOGGER.error(f"Error getting source pals: {traceback.format_exc()}")
        # 确保在发生错误时也恢复原存档
        if current_save:
            LOGGER.info(f"\nReopening original save after error: {current_save}")
            try:
                SaveManager().open(current_save)
            except Exception as restore_error:
                LOGGER.error(f"Error restoring original save: {traceback.format_exc()}")
        return reply(1, None, f"Error getting source pals: {str(e)}")


@pal_blueprint.route("/transfer_pal", methods=["POST"])
@jwt_required()
def transfer_pal():
    source_save = request.json.get("source_save")
    pal_guid = request.json.get("pal_guid")
    
    if not all([source_save, pal_guid]):
        LOGGER.error("Missing required parameters")
        return reply(1, None, "Missing required parameters")
    
    # 保存当前存档路径
    current_save = None
    try:
        # 获取当前存档的所有信息，用于后续恢复
        current_manager = SaveManager()
        current_save = current_manager._file_path
        
        # 打开源存档并获取帕鲁数据
        LOGGER.info(f"\nOpening source save at: {source_save}")
        current_manager.open(source_save)
        
        # 查找并获取帕鲁数据
        source_pal = None
        for player in current_manager.get_players():
            if pal := player.get_pal(pal_guid, disable_warning=True):
                source_pal = pal
                LOGGER.info(f"\nFound pal: {pal.DisplayName} (Level {pal.Level})")
                break
                
        if not source_pal:
            LOGGER.error(f"Source pal {pal_guid} not found in source save")
            return reply(1, None, f"Source pal {pal_guid} not found")
                
        # 获取帕鲁的完整数据
        pal_data = source_pal.dump_obj()
        
        # 重新打开原存档
        LOGGER.info(f"\nReopening original save: {current_save}")
        current_manager.open(current_save)
        
        # 直接返回dump数据
        return reply(0, {"pal_data": pal_data})
            
    except Exception as e:
        LOGGER.error(f"Error getting pal data: {traceback.format_exc()}")
        # 确保在发生错误时也恢复原存档
        if current_save:
            try:
                current_manager.open(current_save)
            except Exception as restore_error:
                LOGGER.error(f"Error restoring original save: {traceback.format_exc()}")
        return reply(1, None, f"Error getting pal data: {str(e)}")


@pal_blueprint.route("/complete_transfer", methods=["POST"])
@jwt_required()
def complete_transfer():
    player_uid = request.json.get("player_uid")
    pal_data = request.json.get("pal_data")
    
    if not all([player_uid, pal_data]):
        return reply(1, None, "Missing required parameters")
        
    try:
        # 直接调用import_pal的逻辑
        return import_pal_internal(player_uid, pal_data)
    except Exception as e:
        LOGGER.error(f"Error completing transfer: {traceback.format_exc()}")
        return reply(1, None, f"Error completing transfer: {str(e)}")


def import_pal_internal(player_uid: str, pal_data: dict) -> dict:
    """Internal function for importing pal data"""
    if player_uid == "PAL_BASE_WORKER_BTN":
        LOGGER.warning("Directly importing pal to basecamp is not yet supported.")
        return reply(1, None, f"Directly importing pal to basecamp is not yet supported.")
    
    try:
        # 记录接收到的数据类型和内容
        LOGGER.info("\n=== Starting PAL Import Process ===")
        LOGGER.info(f"Received player_uid: {player_uid}")
        LOGGER.info(f"Received pal_data type: {type(pal_data)}")
        
        # 如果是字符串，尝试解析JSON
        if isinstance(pal_data, str):
            LOGGER.info("Received string data, attempting to parse JSON...")
            try:
                pal_data = json.loads(pal_data)
                LOGGER.info("JSON parsing successful")
            except json.JSONDecodeError as e:
                LOGGER.error(f"Failed to parse JSON: {e}")
                return reply(1, None, f"Invalid JSON format: {str(e)}")
        
        LOGGER.info(f"Processed pal_data type: {type(pal_data)}")
        LOGGER.info(f"Processed pal_data content: {json.dumps(pal_data, indent=2) if pal_data else None}")
        
        # 验证帕鲁数据格式
        if not isinstance(pal_data, dict):
            LOGGER.error(f"Invalid pal data format: expected dict, got {type(pal_data)}")
            LOGGER.error(f"Data content: {pal_data}")
            return reply(1, None, f"Invalid pal data format: must be a JSON object, got {type(pal_data)}")
            
        # 验证帕鲁数据结构
        LOGGER.info("\nValidating PAL data structure...")
        
        # 检查root层级
        if not isinstance(pal_data, dict):
            LOGGER.error("Root level validation failed")
            LOGGER.error(f"Expected dict, got {type(pal_data)}")
            return reply(1, None, "Invalid pal data structure: root must be an object")
            
        # 检查value字段
        if "value" not in pal_data:
            LOGGER.error("Missing 'value' field at root level")
            LOGGER.error(f"Available keys: {list(pal_data.keys())}")
            return reply(1, None, "Invalid pal data structure: missing 'value' field at root")
            
        # 检查RawData层级
        current = pal_data.get("value", {})
        LOGGER.info("Checking 'value' level structure...")
        LOGGER.info(f"Keys available: {list(current.keys())}")
        if not isinstance(current, dict) or "RawData" not in current:
            LOGGER.error("Invalid 'RawData' structure")
            LOGGER.error(f"Current data type: {type(current)}")
            LOGGER.error(f"Available keys: {list(current.keys()) if isinstance(current, dict) else 'N/A'}")
            return reply(1, None, "Invalid pal data structure: missing or invalid 'RawData' field")
            
        # 检查object层级
        current = current.get("RawData", {}).get("value", {})
        LOGGER.info("Checking 'RawData.value' level structure...")
        LOGGER.info(f"Keys available: {list(current.keys())}")
        if not isinstance(current, dict) or "object" not in current:
            LOGGER.error("Invalid 'object' structure")
            LOGGER.error(f"Current data type: {type(current)}")
            LOGGER.error(f"Available keys: {list(current.keys()) if isinstance(current, dict) else 'N/A'}")
            return reply(1, None, "Invalid pal data structure: missing or invalid 'object' field")
            
        # 检查SaveParameter层级
        current = current.get("object", {})
        LOGGER.info("Checking 'object' level structure...")
        LOGGER.info(f"Keys available: {list(current.keys())}")
        if not isinstance(current, dict) or "SaveParameter" not in current:
            LOGGER.error("Invalid 'SaveParameter' structure")
            LOGGER.error(f"Current data type: {type(current)}")
            LOGGER.error(f"Available keys: {list(current.keys()) if isinstance(current, dict) else 'N/A'}")
            return reply(1, None, "Invalid pal data structure: missing or invalid 'SaveParameter' field")
        
        LOGGER.info("\nPAL data structure validation passed")
        
        # 获取目标玩家信息
        target_player = SaveManager().get_player(player_uid)
        if not target_player:
            LOGGER.error(f"Target player {player_uid} not found")
            return reply(1, None, f"Target player {player_uid} not found")
            
        # 记录目标玩家信息
        LOGGER.info(f"\nTarget player info:")
        LOGGER.info(f"  - Name: {target_player.NickName}")
        LOGGER.info(f"  - PlayerUId: {target_player.PlayerUId}")
        LOGGER.info(f"  - GroupId: {target_player.group_id}")
        
        # 首先创建一个基础PAL实体
        LOGGER.info("\nCreating base PAL entity...")
        base_pal = SaveManager().add_pal(str(target_player.PlayerUId), None, is_import=True)
        if not base_pal:
            LOGGER.error("Failed to create base PAL entity")
            return reply(1, None, "Failed to create base PAL entity")
        
        base_data = base_pal._pal_obj
        
        # 从导入数据中提取关键信息
        import_param = pal_data.get("value", {}).get("RawData", {}).get("value", {}).get("object", {}).get("SaveParameter", {}).get("value", {})
        
        # 更新基础PAL的属性
        base_param = base_data["value"]["RawData"]["value"]["object"]["SaveParameter"]["value"]
        
        # 保留这些关键ID不变
        preserved_keys = ["InstanceId", "OwnerPlayerUId", "group_id", "ContainerId", "SlotIndex", 
                         "EquipItemContainerId", "OwnedPalStorageContainerId", "OtomoCharacterContainerId"]
        preserved_values = {k: base_param[k] for k in preserved_keys if k in base_param}
        
        # 更新其他属性
        update_keys = ["CharacterID", "Level", "Rank", "Rank_HP", "Rank_Attack", "Rank_Defence", 
                      "Rank_CraftSpeed", "Talent_HP", "Talent_Melee", "Talent_Shot", "Talent_Defense",
                      "PassiveSkillList", "EquipWaza", "MasteredWaza", "Gender", "HasTowerVariant"]
                      
        LOGGER.info("\nUpdating PAL properties...")
        for key in update_keys:
            if key in import_param:
                LOGGER.info(f"  - Updating {key}")
                base_param[key] = copy.deepcopy(import_param[key])
        
        # 恢复保留的值
        for key, value in preserved_values.items():
            base_param[key] = value
            
        # 设置昵称
        base_param["NickName"] = {
            "type": "StrProperty",
            "value": import_param.get("NickName", {}).get("value", "Imported PAL")
        }
        
        # 使用更新后的数据重新创建PAL实体
        LOGGER.info("\nRecreating PAL entity with updated data...")
        pal_entity = SaveManager().add_pal(str(target_player.PlayerUId), base_data, is_import=True)
        if not pal_entity:
            LOGGER.error("Failed to recreate PAL entity")
            return reply(1, None, f"Failed importing pal, likely your pal containers are full, check logs for detail.")
            
        # 删除原始的基础PAL
        LOGGER.info("\nCleaning up base PAL...")
        SaveManager().delete_pal(base_pal.InstanceId)
            
        LOGGER.info(f"\nSuccessfully imported pal:")
        LOGGER.info(f"  - NickName: {pal_entity.NickName}")
        LOGGER.info(f"  - group_id: {pal_entity.group_id}")
        LOGGER.info(f"  - OwnerPlayerUId: {pal_entity.OwnerPlayerUId}")
        
        return reply(0, _pal_data(pal_entity))
            
    except Exception as e:
        stack_trace = traceback.format_exc()
        LOGGER.error(f"Error importing pal: {stack_trace}")
        return reply(1, None, f"Error happened during importing pal, check logs for detail. {stack_trace}")


@pal_blueprint.route("/import_pal", methods=["POST"])
@jwt_required()
def import_pal():
    PlayerUId = request.json.get("PlayerUId")
    pal_data = request.json.get("pal_data")
    return import_pal_internal(PlayerUId, pal_data)
