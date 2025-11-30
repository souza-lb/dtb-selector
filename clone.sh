#!/usr/bin/env bash
set -euo pipefail

# =============== 路径配置（可按需调整）===============
QUIRKS_DIR="/home/ark/.quirks"     # 目标机型库
CONSOLE_FILE="/boot/.console"      # 当前生效机型标记

# =============== 小工具函数（英文输出 / 中文注释）===============
msg()  { echo "[clone.sh] $*"; }
warn() { echo "[clone.sh][WARN] $*" >&2; }
err()  { echo "[clone.sh][ERR ] $*" >&2; }

# 读当前 .console 内容，小工具函数，避免重复
get_console_label() {
  tr -d '\r\n' < "$CONSOLE_FILE" 2>/dev/null || true
}

# 先读取已有 .console，作为默认机型，避免未知 DTB 把原有配置改成 r36s
CUR_VAL="$(get_console_label)"
DEFAULT_LABEL="${CUR_VAL:-r36s}"

# =============== DTB -> LABEL 映射（按你的表）===============
# 从 /boot/boot.ini 中匹配：load mmc 1:1 ${dtb_loadaddr} <DTB>
BOOTINI="/boot/boot.ini"
DTB=""

if [[ -r "$BOOTINI" ]]; then
  # 容忍失败：整条管道最后加 || true
  DTB="$(
    grep -oE 'load[[:space:]]+mmc[[:space:]]+1:1[[:space:]]+\$\{dtb_loadaddr\}[[:space:]]+[[:graph:]]+' "$BOOTINI" \
    | awk '{print $NF}' \
    | tail -n1 \
    | xargs -r basename \
    || true
  )"
else
  warn "boot.ini not readable: $BOOTINI"
fi

declare -A dtb2label=(
  [rk3326-mymini-linux.dtb]=mymini
  [rk3326-xf35h-linux.dtb]=xf35h
  [rk3326-r36pro-linux.dtb]=r36pro
  [rk3326-r36max-linux.dtb]=r36max
  [rk3326-xf40h-linux.dtb]=xf40h
  [rk3326-dc40v-linux.dtb]=dc40v
  [rk3326-dc35v-linux.dtb]=dc35v
  [rk3326-r36h-linux.dtb]=r36h
  [rk3326-r36plus-linux.dtb]=r36splus
  [rk3326-r46h-linux.dtb]=r46h
  [rk3326-r40xx-linux.dtb]=r40xx
  [rk3326-hg36-linux.dtb]=hg36
  [rk3326-rx6h-linux.dtb]=rx6h
  [rk3326-k36s-linux.dtb]=k36s
  [rk3326-r36tmax-linux.dtb]=r36tmax
  [rk3326-t16max-linux.dtb]=t16max
  [rk3326-r36ultra-linux.dtb]=r36ultra
  [rk3326-xgb36-linux.dtb]=xgb36
  [rk3326-a10mini-linux.dtb]=a10mini
)

declare -A console_profile=(
  [mymini]=480p
  [xf35h]=480p
  [r36pro]=480p
  [r36max]=720p
  [xf40h]=720p
  [dc40v]=720p
  [dc35v]=480p
  [r36h]=480p
  [r36splus]=720p
  [r46h]=768p
  [r40xx]=768p
  [hg36]=480p
  [rx6h]=480p
  [k36s]=480p
  [r36tmax]=720p
  [t16max]=720p
  [r36ultra]=720p
  [xgb36]=480p
  [a10mini]=480p
  [r36s]=480p
)

declare -A joy_conf_map=(
  [mymini]=single
  [xf35h]=dual
  [r36pro]=dual
  [r36max]=dual
  [xf40h]=dual
  [dc40v]=dual
  [dc35v]=dual
  [r36h]=dual
  [r36splus]=dual
  [r46h]=dual
  [r40xx]=dual
  [hg36]=dual
  [rx6h]=dual
  [k36s]=single
  [r36tmax]=dual
  [t16max]=dual
  [r36ultra]=dual
  [xgb36]=single
  [a10mini]=none
  [r36s]=dual
)

declare -A ogage_conf_map=(
  [mymini]=select
  [xf35h]=select
  [r36pro]=happy5
  [r36max]=happy5
  [xf40h]=select
  [dc40v]=happy5
  [dc35v]=happy5
  [r36h]=select
  [r36splus]=happy5
  [r46h]=select
  [r40xx]=happy5
  [hg36]=happy5
  [rx6h]=select
  [k36s]=happy5
  [r36tmax]=happy5
  [t16max]=happy5
  [r36ultra]=happy5
  [xgb36]=happy5
  [a10mini]=happy5
  [r36s]=happy5
)

rk915_set=("xf40h" "dc40v" "xf35h" "dc35v" "r36ultra" "k36s" "r36tmax") # 按需增删
ga_set=("mymini" "xgb36")                                               # 按需增删
spi_set=("dc35v" "dc40v")                                               # 按需增删

# LABEL：优先用 DTB 映射；没有映射就退回 r36s
LABEL="${dtb2label[$DTB]:-r36s}"

# 如果源存在则复制；isfile=yes 时以文件目标安装（保持权限 0755）
cp_if_exists() {
  local src="$1" dst="$2" isfile="${3:-no}"

  if [[ -e "$src" ]]; then
    if [[ "$isfile" == "yes" ]]; then
      mkdir -p "$(dirname "$dst")"
      # 保留属主/属组/时间戳等
      if cp -a "$src" "$dst" 2>/dev/null; then
        :
      else
        # 极端情况下的兜底：还用 install，但把所有权按源文件纠正回去
        install -m 0755 -D "$src" "$dst"
        sudo chown --reference="$src" "$dst" 2>/dev/null || true
        sudo touch -r "$src" "$dst" 2>/dev/null || true
      fi
      # 统一权限为 0755（不影响属主/属组）
      sudo chmod 0755 "$dst" || true
    else
      mkdir -p "$dst"
      cp -a "$src" "$dst/"
    fi
    msg "Copied: $src -> $dst"
  else
    warn "Source not found, skip: $src"
  fi
}

link_drastic_dir() {
  local name="$1"
  local src="/roms/nds/$name"
  local dst="/opt/drastic/$name"

  # 如果源目录不存在则创建一个空目录
  if [[ ! -d "$src" ]]; then
    msg "Source $src not found, creating it..."
    sudo mkdir -p "$src" || warn "Failed to create $src"
  fi

  # 删除旧的目录或符号链接（不让失败导致脚本退出）
  if [[ -e "$dst" || -L "$dst" ]]; then
    msg "Remove old $dst"
    sudo rm -rf "$dst" || warn "Failed to remove $dst"
  fi

  # 创建新的符号链接
  if sudo ln -s "$src" "$dst"; then
    msg "Linked: $dst -> $src"
  else
    warn "Failed to create symlink: $dst -> $src"
  fi
}

apply_hotkey_conf() {
  local dtbval="$1" kind ogage_conf ra_conf ra32_conf
  # 键不存在时，kind 为空串（避免 set -u 爆炸）
  kind="${ogage_conf_map[$dtbval]:-}"

  case "$kind" in
    select)
      ogage_conf="$QUIRKS_DIR/ogage.select.conf"
      ra_conf="$QUIRKS_DIR/retroarch64.cfg"
      ra32_conf="$QUIRKS_DIR/retroarch32.cfg"
      ;;
    happy5)
      ogage_conf="$QUIRKS_DIR/ogage.happy5.conf"
      ra_conf="$QUIRKS_DIR/retroarch64.cfg"
      ra32_conf="$QUIRKS_DIR/retroarch32.cfg"
      ;;
    *)
      ogage_conf=""
      ra_conf=""
      ra32_conf=""
      ;;
  esac

  if [[ -n "$ogage_conf" ]]; then
    msg "change hotkey: $dtbval -> $(basename "$ogage_conf")"
    cp_if_exists "$ogage_conf" "/home/ark/ogage.conf" "yes"
  else
    msg "hotkey unchanged for: $dtbval (no mapping)"
  fi

  if [[ -n "$ra_conf" ]]; then
    msg "change hotkey: $dtbval -> $(basename "$ra_conf")"
    cp_if_exists "$ra_conf" "/home/ark/.config/retroarch/retroarch.cfg" "yes"
  else
    msg "hotkey unchanged for: $dtbval (no mapping)"
  fi

  if [[ -n "$ra32_conf" ]]; then
    msg "change hotkey: $dtbval -> $(basename "$ra32_conf")"
    cp_if_exists "$ra32_conf" "/home/ark/.config/retroarch32/retroarch.cfg" "yes"
  else
    msg "hotkey unchanged for: $dtbval (no mapping)"
  fi
}

adjust_per_joy_conf() {
  local dtbval="$1" prof
  # 键不存在时，prof 为空串（避免 set -u 爆炸）
  prof="${joy_conf_map[$dtbval]:-}"

  case "$prof" in
    none|single)
      cp_if_exists "$QUIRKS_DIR/noneJoy/controls.ini"     "/roms/psp/ppsspp/PSP/SYSTEM/controls.ini"       "yes"
      cp_if_exists "$QUIRKS_DIR/noneJoy/ppsspp.ini"       "/roms/psp/ppsspp/PSP/SYSTEM/ppsspp.ini"         "yes"
      cp_if_exists "$QUIRKS_DIR/noneJoy/ppsspp.ini.sdl"   "/roms/psp/ppsspp/PSP/SYSTEM/ppsspp.ini.sdl"     "yes"
      [[ -d "/roms2/psp" ]] && cp_if_exists "$QUIRKS_DIR/noneJoy/controls.ini"   "/roms2/psp/ppsspp/PSP/SYSTEM/controls.ini"   "yes" || true
      [[ -d "/roms2/psp" ]] && cp_if_exists "$QUIRKS_DIR/noneJoy/ppsspp.ini"     "/roms2/psp/ppsspp/PSP/SYSTEM/ppsspp.ini"     "yes" || true
      [[ -d "/roms2/psp" ]] && cp_if_exists "$QUIRKS_DIR/noneJoy/ppsspp.ini.sdl" "/roms2/psp/ppsspp/PSP/SYSTEM/ppsspp.ini.sdl" "yes" || true
      ;;
    dual)
      cp_if_exists "$QUIRKS_DIR/dualJoy/controls.ini"     "/roms/psp/ppsspp/PSP/SYSTEM/controls.ini"       "yes"
      cp_if_exists "$QUIRKS_DIR/dualJoy/ppsspp.ini"       "/roms/psp/ppsspp/PSP/SYSTEM/ppsspp.ini"         "yes"
      cp_if_exists "$QUIRKS_DIR/dualJoy/ppsspp.ini.sdl"   "/roms/psp/ppsspp/PSP/SYSTEM/ppsspp.ini.sdl"     "yes"
      [[ -d "/roms2/psp" ]] && cp_if_exists "$QUIRKS_DIR/dualJoy/controls.ini"   "/roms2/psp/ppsspp/PSP/SYSTEM/controls.ini"   "yes" || true
      [[ -d "/roms2/psp" ]] && cp_if_exists "$QUIRKS_DIR/dualJoy/ppsspp.ini"     "/roms2/psp/ppsspp/PSP/SYSTEM/ppsspp.ini"     "yes" || true
      [[ -d "/roms2/psp" ]] && cp_if_exists "$QUIRKS_DIR/dualJoy/ppsspp.ini.sdl" "/roms2/psp/ppsspp/PSP/SYSTEM/ppsspp.ini.sdl" "yes" || true
      ;;
    *)
      msg "No profile assets for: ${prof:-<empty>} (dtbval=$dtbval)"
      ;;
  esac
}

apply_profile_assets() {
  local cur prof
  cur="$(get_console_label)"
  [[ -n "$cur" ]] || return 0

  prof="${console_profile[$cur]:-}"
  if [[ "$prof" =~ ^(480p|720p|768p)$ ]]; then
    cp_if_exists "$QUIRKS_DIR/$prof/351Files" "/opt/351Files" "no"
  else
    msg "No profile assets for: ${prof:-$cur}"
  fi
}

apply_es_input() {
  [[ -f "$CONSOLE_FILE" ]] || return 0

  local cur_console use_ga="false"
  cur_console="$(get_console_label)"

  for x in "${ga_set[@]}"; do
    if [[ "$cur_console" == "$x" ]]; then
      use_ga="true"
      break
    fi
  done

  if [[ "$use_ga" == "true" ]]; then
    cp_if_exists "$QUIRKS_DIR/es_input_ga.cfg" "/etc/emulationstation/es_input.cfg" "yes"
    cp_if_exists "$QUIRKS_DIR/retroarch64_ga.cfg" "/home/ark/.config/retroarch/retroarch.cfg" "yes"
    cp_if_exists "$QUIRKS_DIR/retroarch32_ga.cfg" "/home/ark/.config/retroarch32/retroarch.cfg" "yes"
  else
    cp_if_exists "$QUIRKS_DIR/es_input_gs.cfg" "/etc/emulationstation/es_input.cfg" "yes"
  fi
}

# 依据 LABEL 执行
apply_quirks_for() {
  local dtbval="$1"
  adjust_per_joy_conf "$dtbval"
  apply_hotkey_conf "$dtbval"
  apply_profile_assets
  apply_es_input
}

# =============== 执行开始 ===============
msg "DTB filename: ${DTB:-<empty>}, LABEL: $LABEL"

# 按规则处理 /boot/.console
if [[ ! -f "$CONSOLE_FILE" ]]; then
  clear
  echo "==============================="
  echo "   arkos for clone lcdyk  ..."
  echo "==============================="
  sleep 2
  link_drastic_dir backup
  link_drastic_dir cheats
  link_drastic_dir savestates
  link_drastic_dir slot2
  echo "$LABEL" > "$CONSOLE_FILE"
  msg "Wrote new console file: $CONSOLE_FILE -> $LABEL"
  apply_quirks_for "$LABEL"
  sleep 5
  systemctl status systemd-journald.service systemd-journald.socket || true
  sudo systemctl unmask systemd-journald.service systemd-journald.socket || true
  sudo systemctl enable --now systemd-journald.service systemd-journald.socket || true
else
  CUR_VAL="$(get_console_label)"
  if [[ "$CUR_VAL" == "$LABEL" ]]; then
    msg "Console unchanged ($CUR_VAL); nothing to do."
  else
    (
      # ==== 所有输出都到 tty1 ====
      # 复位/清屏并回到左上角
      printf '\033c'
      echo "==============================="
      echo "   arkos for clone lcdyk  ..."
      echo "==============================="
      echo
      echo "[firstboot.sh] old config: ${CUR_VAL}"
      echo "[firstboot.sh] new config: ${LABEL}"
      echo
      # 顺序保持不变：先写 .console，再应用 quirks（避免重入时再次触发）
      echo "$LABEL" | sudo tee "$CONSOLE_FILE" > /dev/null
      apply_quirks_for "$LABEL"
      sleep 5
    ) > /dev/tty1 2>&1
    systemctl status systemd-journald.service systemd-journald.socket || true
    sudo systemctl unmask systemd-journald.service systemd-journald.socket || true
    sudo systemctl enable --now systemd-journald.service systemd-journald.socket || true
  fi
fi

# 加载驱动
sudo depmod -a || true

# 安装 915 wifi 驱动
if [[ -f "$CONSOLE_FILE" ]]; then
  cur_console="$(get_console_label)"
  for x in "${rk915_set[@]}"; do
    if [[ "$cur_console" == "$x" ]]; then
      msg "insmod rk915.ko: $cur_console"
      sudo modprobe -v rk915 || true
      break
    fi
  done
fi

# ws2812 摇杆灯控制加载 spi 模块
if [[ -f "$CONSOLE_FILE" ]]; then
  cur_console="$(get_console_label)"
  for x in "${spi_set[@]}"; do
    if [[ "$cur_console" == "$x" ]]; then
      msg "sudo modprobe spidev : $cur_console"
      sudo modprobe spidev || true
      break
    fi
  done
fi

sudo modprobe -v mt7610u_sta || true

# 开机将音频设置为 SPK 如果是 OFF 的话
STATE="$(
  amixer get 'Playback Path' 2>/dev/null | grep -oP "Item0: '\K\w+" || true
)"

if [[ "$STATE" = "OFF" ]]; then
  echo "Playback Path is OFF, switching to SPK..."
  amixer set 'Playback Path' 'SPK' || true
  sudo alsactl store || true
else
  echo "Playback Path is already set to ${STATE:-UNKNOWN}, no change."
fi

# 简体中文首启配置
# Adição suporte a pt_BR
if [[ -f "/boot/.br" ]]; then
  if grep -q "Language" /home/ark/.emulationstation/es_settings.cfg; then
    sed -i -e '/<string name\=\"Language/c\<string name\=\"Language\" value\=\"br\" \/>' /home/ark/.emulationstation/es_settings.cfg || true
  else
    sed -i '$a <string name\=\"Language\" value\=\"br\" \/>' /home/ark/.emulationstation/es_settings.cfg || true
  fi
fi

if [[ -f "/boot/.cn" ]]; then
  if grep -q "Language" /home/ark/.emulationstation/es_settings.cfg; then
    sed -i -e '/<string name\=\"Language/c\<string name\=\"Language\" value\=\"zh-CN\" \/>' /home/ark/.emulationstation/es_settings.cfg || true
  else
    sed -i '$a <string name\=\"Language\" value\=\"zh-CN\" \/>' /home/ark/.emulationstation/es_settings.cfg || true
  fi

  cp_if_exists "$QUIRKS_DIR/option-gamelist.xml" "/opt/system/gamelist.xml" "yes"
  sudo rm -f /etc/localtime || true
  sudo ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime || true

  sudo sed -i -e '/Language \= en_US/c\Language \= zh_CN' /opt/ppsspp/backupforromsfolder/ppsspp/PSP/SYSTEM/ppsspp.ini      || true
  sudo sed -i -e '/Language \= en_US/c\Language \= zh_CN' /opt/ppsspp/backupforromsfolder/ppsspp/PSP/SYSTEM/ppsspp.ini.go   || true
  sudo sed -i -e '/Language \= en_US/c\Language \= zh_CN' /opt/ppsspp/backupforromsfolder/ppsspp/PSP/SYSTEM/ppsspp.ini.sdl  || true

  sed -i -e '/Language \= en_US/c\Language \= zh_CN' /roms/psp/ppsspp/PSP/SYSTEM/ppsspp.ini      || true
  sed -i -e '/Language \= en_US/c\Language \= zh_CN' /roms/psp/ppsspp/PSP/SYSTEM/ppsspp.ini.go   || true
  sed -i -e '/Language \= en_US/c\Language \= zh_CN' /roms/psp/ppsspp/PSP/SYSTEM/ppsspp.ini.sdl  || true

  sed -i -e '/user_language \= \"/c\user_language \= \"12\"' /home/ark/.config/retroarch32/retroarch.cfg        || true
  sed -i -e '/user_language \= \"/c\user_language \= \"12\"' /home/ark/.config/retroarch/retroarch.cfg          || true
  sed -i -e '/user_language \= \"/c\user_language \= \"12\"' /home/ark/.config/retroarch32/retroarch.cfg.bak    || true
  sed -i -e '/user_language \= \"/c\user_language \= \"12\"' /home/ark/.config/retroarch/retroarch.cfg.bak      || true

  sed -i -e '/menu_driver \= \"/c\menu_driver \= \"ozone\"' /home/ark/.config/retroarch32/retroarch.cfg        || true
  sed -i -e '/menu_driver \= \"/c\menu_driver \= \"ozone\"' /home/ark/.config/retroarch/retroarch.cfg          || true
  sed -i -e '/menu_driver \= \"/c\menu_driver \= \"ozone\"' /home/ark/.config/retroarch32/retroarch.cfg.bak    || true
  sed -i -e '/menu_driver \= \"/c\menu_driver \= \"ozone\"' /home/ark/.config/retroarch/retroarch.cfg.bak      || true

  sudo rm -f /boot/.cn || true
fi

if [[ -x /home/ark/.config/lastgame.sh ]]; then
  sudo -u ark /home/ark/.config/lastgame.sh
fi

msg "Done."
exit 0
