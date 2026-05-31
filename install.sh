#!/bin/bash
repo=klipper_addon_de
repo_path="$(cd "$(dirname "$0")" && pwd)"


# Exit if root
if [ "$(id -u)" = "0" ]; then
    echo "Script must run from non-root !!!"
    exit 1
fi


module_name1="ratos_hybrid_corexy.py"
module_name2="extruder_de.py"
module_name3="z_tilt_de.py"
module_name4="beacon_adaptive_heat_soak.py"
module_name5="beacon_adaptive_heat_soak_model_training.csv"
module_name6="beacon_true_zero_correction.py"
beacon_name="beacon.py"
motorsync_name="motors_sync.py"

klipper_path="$HOME/klipper"
klipper_env_path="$HOME/klippy-env"
extras_path=${klipper_path}/klippy/extras/
kinematics_path=${klipper_path}/klippy/kinematics/
beacon_path=$repo_path"/beacon"
motorsync_path=$repo_path"/motors-sync"

# Linking
ln -sf "$repo_path/$module_name1" "${kinematics_path}${module_name1}"
ln -sf "$repo_path/$module_name2" "${kinematics_path}${module_name2}"
ln -sf "$repo_path/$module_name3" "${extras_path}${module_name3}"
ln -sf "$repo_path/$module_name4" "${extras_path}${module_name4}"
ln -sf "$repo_path/$module_name5" "${extras_path}${module_name5}"
ln -sf "$repo_path/$module_name6" "${extras_path}${module_name6}"
ln -sf "$beacon_path/$beacon_name" "${extras_path}${beacon_name}"
ln -sf "$motorsync_path/$motorsync_name" "${extras_path}${motorsync_name}"

# Add to .git/info/exclude if not already present
exclude_file="${klipper_path}/.git/info/exclude"
exclude_entry1="klippy/kinematics/${module_name1}"
exclude_entry2="klippy/kinematics/${module_name2}"
exclude_entry3="klippy/extras/${module_name3}"
exclude_entry4="klippy/extras/${module_name4}"
exclude_entry5="klippy/extras/${module_name5}"
exclude_entry6="klippy/extras/${module_name6}"
exclude_beacon="klippy/extras/${beacon_name}"
exclude_motorsync="klippy/extras/${motorsync_name}"
if ! grep -qxF "$exclude_entry1" "$exclude_file"; then
    echo "$exclude_entry1" >> "$exclude_file"
fi
if ! grep -qxF "$exclude_entry2" "$exclude_file"; then
    echo "$exclude_entry2" >> "$exclude_file"
fi
if ! grep -qxF "$exclude_entry3" "$exclude_file"; then
    echo "$exclude_entry3" >> "$exclude_file"
fi
if ! grep -qxF "$exclude_entry4" "$exclude_file"; then
    echo "$exclude_entry4" >> "$exclude_file"
fi
if ! grep -qxF "$exclude_entry5" "$exclude_file"; then
    echo "$exclude_entry5" >> "$exclude_file"
fi
if ! grep -qxF "$exclude_entry6" "$exclude_file"; then
    echo "$exclude_entry6" >> "$exclude_file"
fi
if ! grep -qxF "$exclude_beacon" "$exclude_file"; then
    echo "$exclude_beacon" >> "$exclude_file"
fi
if ! grep -qxF "$exclude_motorsync" "$exclude_file"; then
    echo "$exclude_motorsync" >> "$exclude_file"
fi

blk_path=~/printer_data/config/moonraker.conf
# Include update block in moonraker.conf
if [ -f "$blk_path" ]; then
    if ! grep -q "^\[update_manager $repo\]$" "$blk_path"; then
        read -p " Do you want to install updater? (y/n): " answer
        if [ "$answer" != "${answer#[Yy]}" ]; then
          sudo service moonraker stop
          sed -i "\$a \ " "$blk_path"
          sed -i "\$a [update_manager $repo]" "$blk_path"
          sed -i "\$a type: git_repo" "$blk_path"
          sed -i "\$a path: $repo_path" "$blk_path"
          sed -i "\$a origin: https://github.com/DLR3D/klipper_addon_de.git" "$blk_path"
          sed -i "\$a primary_branch: main" "$blk_path"
          sed -i "\$a managed_services: klipper" "$blk_path"
		  sed -i "\$a virtualenv: $HOME/klippy-env/" "$blk_path"
          # echo "Including [update_manager] to $blk_path successfully complete"
          sudo service moonraker start
        else
          echo "Installing updater aborted"
        fi
    else
        echo "Including [update_manager] aborted, [update_manager] already exists in $blk_path"
    fi
fi

sudo apt update


echo "Adaptive Heatsoak: installing python requirements to env."
"${klipper_env_path}/bin/pip" install pygam

echo "Motor Sync: installing requirements."
sudo apt install libatlas-base-dev libopenblas-dev

# install beacon requirements to env
echo "beacon: installing python requirements to env."
"${klipper_env_path}/bin/pip" install -r "${beacon_path}/requirements.txt"
echo "beacon: Updating firmware."
"$klipper_env_path/bin/python" "$beacon_path/update_firmware.py" update all

echo "Installation successful restarting klipper now."
sudo service klipper stop
sudo service klipper start