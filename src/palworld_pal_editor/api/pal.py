import copy
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import traceback

from palworld_pal_editor.utils.util import reply

from palworld_pal_editor.core import SaveManager, PalEntity
from palworld_pal_editor.utils import LOGGER

pal_blueprint = Blueprint("pal", __name__)


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
    target_player_uid = request.json.get("target_player_uid")
    
    LOGGER.info("\n=== Starting Pal Transfer Process ===")
    LOGGER.info(f"Source save path: {source_save}")
    LOGGER.info(f"Target player UID: {target_player_uid}")
    LOGGER.info(f"Pal GUID to transfer: {pal_guid}")
    
    if not all([source_save, pal_guid, target_player_uid]):
        LOGGER.error("Missing required parameters")
        return reply(1, None, "Missing required parameters")
    
    # 保存当前存档路径
    current_save = None
    try:
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
        
        # 打开源存档并获取帕鲁数据
        LOGGER.info("\n=== Opening Source Save and Getting Pal Data ===")
        LOGGER.info(f"Opening source save at: {source_save}")
        current_manager.open(source_save)
        
        source_pal = None
        for player in current_manager.get_players():
            if pal := player.get_pal(pal_guid, disable_warning=True):
                source_pal = pal
                LOGGER.info(f"\nFound source pal:")
                LOGGER.info(f"  - Display Name: {pal.DisplayName}")
                LOGGER.info(f"  - Character ID: {pal.CharacterID}")
                LOGGER.info(f"  - Instance ID: {pal.InstanceId}")
                LOGGER.info(f"  - Owner: {player.NickName} ({player.PlayerUId})")
                LOGGER.info(f"  - Container ID: {pal.ContainerId}")
                LOGGER.info(f"  - Slot Index: {pal.SlotIndex}")
                break
                
        if not source_pal:
            LOGGER.error(f"Source pal {pal_guid} not found in source save")
            # 重新打开原存档
            LOGGER.info(f"\nReopening original save: {current_save}")
            current_manager.open(current_save)
            return reply(1, None, f"Source pal {pal_guid} not found")
            
        # 获取并记录帕鲁的完整数据
        pal_data = source_pal.dump_obj()
        LOGGER.info("\nPal data dump:")
        LOGGER.info(pal_data)
        
        # 重新打开原存档
        LOGGER.info(f"\nReopening original save: {current_save}")
        current_manager.open(current_save)
        
        # 验证原存档是否正确恢复
        restored_players = current_manager.get_players()
        LOGGER.info("\nVerifying restored save:")
        for player in restored_players:
            LOGGER.info(f"  Player: {player.NickName} - {player.PlayerUId}")
        
        return reply(0, _pal_data(source_pal))
            
    except Exception as e:
        LOGGER.error("\n=== Transfer Failed ===")
        LOGGER.error(f"Error getting pal data: {traceback.format_exc()}")
        # 确保在发生错误时也恢复原存档
        if current_save:
            LOGGER.info(f"\nReopening original save after error: {current_save}")
            try:
                SaveManager().open(current_save)
            except Exception as restore_error:
                LOGGER.error(f"Error restoring original save: {traceback.format_exc()}")
        return reply(1, None, f"Error getting pal data: {str(e)}")
        
    return reply(0)


@pal_blueprint.route("/import_pal", methods=["POST"])
@jwt_required()
def import_pal():
    PlayerUId = request.json.get("PlayerUId")
    pal_data = request.json.get("pal_data")
    
    if PlayerUId == "PAL_BASE_WORKER_BTN":
        LOGGER.warning("Directly importing pal to basecamp is not yet supported.")
        return reply(1, None, f"Directly importing pal to basecamp is not yet supported.")
    
    try:
        # 创建一个新的数据副本，以便修改
        import_data = copy.deepcopy(pal_data)
        
        # 保存原始昵称
        original_nickname = import_data.get("NickName") or import_data.get("DisplayName", "")
        
        # 更新所有者ID
        import_data["OwnerPlayerUId"] = PlayerUId
        
        # 生成新的 group_id
        import_data["group_id"] = None  # 让系统自动生成新的 group_id
        
        # 创建帕鲁实体
        pal_entity = SaveManager().add_pal(PlayerUId, import_data)
        if not pal_entity:
            return reply(
                1,
                None,
                f"Failed importing pal, likely your pal containers are full, check logs for detail.",
            )
            
        # 立即更新昵称，覆盖 "!!!DUPED PAL!!!"
        try:
            pal_entity.NickName = original_nickname
            LOGGER.info(f"Successfully restored original nickname: {original_nickname}")
        except Exception as e:
            LOGGER.error(f"Failed to restore original nickname: {e}")
            
    except Exception as e:
        stack_trace = traceback.format_exc()
        LOGGER.error(f"Error importing pal: {stack_trace}")
        return reply(
            1,
            None,
            f"Error happened during importing pal, check logs for detail. {stack_trace}",
        )
    
    return reply(0, _pal_data(pal_entity))
