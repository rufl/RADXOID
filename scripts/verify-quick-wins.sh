#!/bin/bash
# RADXOID - Verify Quick Wins on Device
# Usage: ./scripts/verify-quick-wins.sh [adb-serial]
# Example: ./scripts/verify-quick-wins.sh USB12345678

if [ -z "$1" ]; then
    echo "Usage: $0 [adb-serial]"
    echo "Example: $0 USB12345678"
    exit 1
fi

SERIAL="$1"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  RADXOID - Verifying Quick Wins on Device: $SERIAL                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Test ADB connection
echo -e "${YELLOW}🔍 Testing ADB connection...${NC}"
if ! adb -s "$SERIAL" devices | grep -q "$SERIAL"; then
    echo -e "${RED}❌ Error: Device $SERIAL not found or not connected${NC}"
    exit 1
fi
echo -e "${GREEN}✅ ADB connected to $SERIAL${NC}"
echo ""

# Check 1: Zram Compression
echo -e "${GREEN}1. Zram Compression:${NC}"
ZRAM_COMP=$(adb -s "$SERIAL" shell cat /proc/sys/vm/zram_compression 2>/dev/null || echo "NOT_AVAILABLE")
if [ "$ZRAM_COMP" = "lz4" ]; then
    echo -e "   ✅ Zram compression: $ZRAM_COMP"
else
    echo -e "   ⚠️  Zram compression: $ZRAM_COMP (expected: lz4)"
fi
echo ""

# Check 2: TCP Congestion Control
echo -e "${GREEN}2. TCP Congestion Control:${NC}"
TCP_CC=$(adb -s "$SERIAL" shell cat /proc/sys/net/ipv4/tcp_congestion_control 2>/dev/null || echo "NOT_AVAILABLE")
if [ "$TCP_CC" = "bbr" ]; then
    echo -e "   ✅ TCP congestion control: $TCP_CC"
else
    echo -e "   ⚠️  TCP congestion control: $TCP_CC (expected: bbr)"
fi
echo ""

# Check 3: CPU Frequency
echo -e "${GREEN}3. CPU Frequency Limits:${NC}"
CPU_MAX=$(adb -s "$SERIAL" shell cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq 2>/dev/null || echo "NOT_AVAILABLE")
CPU_MIN=$(adb -s "$SERIAL" shell cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq 2>/dev/null || echo "NOT_AVAILABLE")
echo -e "   Max frequency: $CPU_MAX kHz (expected: 1800000)"
echo -e "   Min frequency: $CPU_MIN kHz (expected: 408000)"
echo ""

# Check 4: LMK
echo -e "${GREEN}4. LMK (Low Memory Killer):${NC}"
LMK_MINFREE=$(adb -s "$SERIAL" shell cat /sys/module/lowmemorykiller/parameters/minfree 2>/dev/null || echo "NOT_AVAILABLE")
echo -e "   LMK minfree: $LMK_MINFREE"
echo ""

# Check 5: ART JIT
echo -e "${GREEN}5. ART JIT Optimizations:${NC}"
JIT_INLINE=$(adb -s "$SERIAL" shell getprop dalvik.vm.jit.inline_depth 2>/dev/null || echo "NOT_AVAILABLE")
JIT_CACHE=$(adb -s "$SERIAL" shell getprop dalvik.vm.jit.code_cache_size 2>/dev/null || echo "NOT_AVAILABLE")
echo -e "   JIT inline depth: $JIT_INLINE (expected: 6)"
echo -e "   JIT code cache size: $JIT_CACHE (expected: 4m)"
echo ""

# Check 6: Zram Streams
echo -e "${GREEN}6. Zram Streams:${NC}"
ZRAM_STREAMS=$(adb -s "$SERIAL" shell cat /sys/block/zram0/num_streams 2>/dev/null || echo "NOT_AVAILABLE")
echo -e "   Zram streams: $ZRAM_STREAMS (expected: 4)"
echo ""

# Check 7: Read-Ahead
echo -e "${GREEN}7. Read-Ahead Size:${NC}"
READ_AHEAD=$(adb -s "$SERIAL" shell cat /sys/block/mmcblk0/queue/read_ahead_kb 2>/dev/null || echo "NOT_AVAILABLE")
echo -e "   Read-ahead: $READ_AHEAD kB (expected: 512)"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  Verification Complete!                                                 ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Quick Wins Status:"
echo "  1. Zram LZ4: $(if [ "$ZRAM_COMP" = "lz4" ]; then echo '✅'; else echo '⚠️'; fi)"
echo "  2. TCP BBR: $(if [ "$TCP_CC" = "bbr" ]; then echo '✅'; else echo '⚠️'; fi)"
echo "  3. CPU Freq: $(if [ "$CPU_MAX" = "1800000" ]; then echo '✅'; else echo '⚠️'; fi)"
echo "  4. LMK: ⚠️ (manual check)"
echo "  5. ART JIT: $(if [ "$JIT_INLINE" = "6" ]; then echo '✅'; else echo '⚠️'; fi)"
echo "  6. Zram Streams: $(if [ "$ZRAM_STREAMS" = "4" ]; then echo '✅'; else echo '⚠️'; fi)"
echo "  7. Read-Ahead: $(if [ "$READ_AHEAD" = "512" ]; then echo '✅'; else echo '⚠️'; fi)"
echo ""
