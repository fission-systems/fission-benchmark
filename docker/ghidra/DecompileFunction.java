// GhidraScript: Decompile multiple functions and print JSON.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.util.ArrayList;

public class DecompileFunction extends GhidraScript {
    private Address parseRequestedAddress(String addrStr) {
        Address addr = currentProgram.getAddressFactory().getAddress(addrStr);
        if (addr == null) {
            if (addrStr.startsWith("0x") || addrStr.startsWith("0X")) {
                addr = currentProgram.getAddressFactory().getAddress(addrStr.substring(2));
            } else {
                addr = currentProgram.getAddressFactory().getAddress("0x" + addrStr);
            }
        }
        return addr;
    }

    private long parseUnsignedOffset(String addrStr) {
        String hex = addrStr.trim();
        if (hex.startsWith("0x") || hex.startsWith("0X")) {
            hex = hex.substring(2);
        }
        return Long.parseUnsignedLong(hex, 16);
    }

    private Function resolveFunction(String addrStr) {
        Address direct = parseRequestedAddress(addrStr);
        Function func = direct == null
            ? null
            : currentProgram.getFunctionManager().getFunctionAt(direct);
        if (func != null) {
            return func;
        }

        // Ghidra rebases PIE ELF programs (commonly to 0x100000), while DWARF
        // and DecBench publish link-time virtual addresses/RVAs such as 0x2dab.
        // Only try image-base-relative resolution for an address below the
        // actual program image base so full VAs remain untouched.
        try {
            Address imageBase = currentProgram.getImageBase();
            long offset = parseUnsignedOffset(addrStr);
            if (imageBase != null && imageBase.getOffset() != 0 &&
                    Long.compareUnsigned(offset, imageBase.getOffset()) < 0) {
                Address rebased = imageBase.add(offset);
                return currentProgram.getFunctionManager().getFunctionAt(rebased);
            }
        } catch (Exception ignored) {
            // Preserve the normal per-address "no function" result below.
        }
        return null;
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0) {
            println("{\"error\": \"no addresses specified\"}");
            return;
        }

        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);

        ArrayList<String> jsonResults = new ArrayList<>();

        for (String addrStr : args) {
            try {
                Function func = resolveFunction(addrStr);
                if (func == null) {
                    jsonResults.add("{\"addr\": \"" + addrStr + "\", \"error\": \"no function at " + addrStr + "\"}");
                    continue;
                }
                DecompileResults res = decomp.decompileFunction(func, 60, monitor);
                if (!res.decompileCompleted()) {
                    jsonResults.add("{\"addr\": \"" + addrStr + "\", \"error\": \"decompile failed\"}");
                    continue;
                }
                String code = res.getDecompiledFunction().getC();
                code = code.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n");
                jsonResults.add("{\"addr\": \"" + addrStr + "\", \"name\": \"" + func.getName() + "\", \"code\": \"" + code + "\"}");
            } catch (Exception e) {
                jsonResults.add("{\"addr\": \"" + addrStr + "\", \"error\": \"" + e.getMessage() + "\"}");
            }
        }

        StringBuilder sb = new StringBuilder();
        sb.append("[");
        for (int i = 0; i < jsonResults.size(); i++) {
            sb.append(jsonResults.get(i));
            if (i < jsonResults.size() - 1) {
                sb.append(",");
            }
        }
        sb.append("]");
        println("===BATCH_RESULT===" + sb.toString());
    }
}
