// GhidraScript: Export function diagnostics in JSON for parity benchmarking.
// Modes:
//   functions
//   metadata
//   disasm | pcode | cfg | bundle   (+ address)
//   multi_bundle                     (+ comma-separated addresses)
// multi_bundle: ONE JVM run for many functions in the already-opened program.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Parameter;
import ghidra.program.model.listing.VariableStorage;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.program.model.pcode.Varnode;
import ghidra.program.model.block.SimpleBlockModel;
import ghidra.program.model.block.CodeBlock;
import ghidra.program.model.block.CodeBlockIterator;
import ghidra.program.model.block.CodeBlockReferenceIterator;
import ghidra.program.model.block.CodeBlockReference;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.DataTypeComponent;
import ghidra.program.model.data.Structure;
import ghidra.program.model.data.TypeDef;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.reloc.Relocation;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.Iterator;

public class ExportParity extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("===RESULT==={\"error\": \"missing mode argument\"}");
            return;
        }

        String mode = args[0];
        if (mode.equals("functions")) {
            emit(exportFunctionsJson());
            return;
        }
        if (mode.equals("metadata")) {
            emit(exportMetadataJson());
            return;
        }

        if (args.length < 2) {
            println("===RESULT==={\"error\": \"missing address argument\"}");
            return;
        }

        if (mode.equals("multi_bundle")) {
            // args[1] = "0xA,0xB,0xC"  (requested entry addresses)
            String[] addrs = args[1].split(",");
            StringBuilder sb = new StringBuilder();
            sb.append("{\"schema\": \"ghidra-parity-multi-bundle-v1\", \"by_addr\": {");
            boolean first = true;
            for (String raw : addrs) {
                String addrStr = raw.trim();
                if (addrStr.isEmpty()) {
                    continue;
                }
                Function func = resolveFunction(addrStr);
                if (func == null) {
                    if (!first) sb.append(",");
                    first = false;
                    sb.append("\"").append(normalizeAddrKey(addrStr)).append("\": ");
                    sb.append("{\"error\": \"no function at ").append(jsonEscape(addrStr)).append("\"}");
                    continue;
                }
                if (!first) sb.append(",");
                first = false;
                // Key by the *requested* address so the client can look up by manifest addr.
                sb.append("\"").append(normalizeAddrKey(addrStr)).append("\": ");
                sb.append(exportBundleObject(func));
            }
            sb.append("}}");
            emit(sb.toString());
            return;
        }

        Function func = resolveFunction(args[1]);
        if (func == null) {
            println("===RESULT==={\"error\": \"no function at " + args[1] + "\"}");
            return;
        }

        if (mode.equals("disasm")) {
            emit(exportDisasmJson(func));
        } else if (mode.equals("pcode")) {
            emit(exportPcodeJson(func));
        } else if (mode.equals("cfg")) {
            emit(exportCfgJson(func));
        } else if (mode.equals("abi")) {
            emit(exportAbiJson(func));
        } else if (mode.equals("types")) {
            emit(exportTypesJson(func));
        } else if (mode.equals("callgraph")) {
            emit(exportCallgraphJson(func));
        } else if (mode.equals("strings")) {
            emit(exportStringsJson(func));
        } else if (mode.equals("dataflow")) {
            emit(exportDataflowJson(func));
        } else if (mode.equals("seh")) {
            emit(exportSehJson(func));
        } else if (mode.equals("bundle")) {
            emit(exportBundleObject(func));
        } else {
            println("===RESULT==={\"error\": \"unknown mode " + mode + "\"}");
        }
    }

    private Function resolveFunction(String addrStr) throws Exception {
        Address addr = currentProgram.getAddressFactory().getAddress(addrStr);
        if (addr == null) {
            // try without 0x / with 0x
            if (addrStr.startsWith("0x") || addrStr.startsWith("0X")) {
                addr = currentProgram.getAddressFactory().getAddress(addrStr.substring(2));
            } else {
                addr = currentProgram.getAddressFactory().getAddress("0x" + addrStr);
            }
        }
        if (addr == null) {
            return null;
        }
        Function func = currentProgram.getFunctionManager().getFunctionAt(addr);
        if (func == null) {
            func = currentProgram.getFunctionManager().getFunctionContaining(addr);
        }
        if (func != null) {
            return func;
        }

        // PIE ELF manifests use link-time virtual addresses/RVAs. Ghidra may
        // load the program at a non-zero base (for example 0x100000), so retry
        // below-base requests relative to the program's actual image base.
        try {
            String hex = addrStr.trim();
            if (hex.startsWith("0x") || hex.startsWith("0X")) {
                hex = hex.substring(2);
            }
            long offset = Long.parseUnsignedLong(hex, 16);
            Address imageBase = currentProgram.getImageBase();
            if (imageBase != null && imageBase.getOffset() != 0 &&
                    Long.compareUnsigned(offset, imageBase.getOffset()) < 0) {
                Address rebased = imageBase.add(offset);
                func = currentProgram.getFunctionManager().getFunctionAt(rebased);
                if (func == null) {
                    func = currentProgram.getFunctionManager().getFunctionContaining(rebased);
                }
            }
        } catch (Exception ignored) {
            // Preserve the original null result for malformed/out-of-range input.
        }
        return func;
    }

    private String normalizeAddrKey(String addrStr) {
        try {
            String hex = addrStr.trim().toLowerCase();
            if (hex.startsWith("0x")) {
                hex = hex.substring(2);
            }
            // canonical 0x + lowercase hex without leading zeros stripped carefully
            long v = Long.parseUnsignedLong(hex, 16);
            return String.format("0x%x", v);
        } catch (Exception e) {
            return addrStr.trim().toLowerCase();
        }
    }

    private String exportBundleObject(Function func) throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        sb.append("\"schema\": \"ghidra-parity-bundle-v1\",");
        sb.append("\"address\": \"0x").append(func.getEntryPoint().toString()).append("\",");
        sb.append("\"name\": \"").append(jsonEscape(func.getName())).append("\",");
        sb.append("\"disasm\": ").append(exportDisasmJson(func)).append(",");
        sb.append("\"pcode\": ").append(exportPcodeJson(func)).append(",");
        sb.append("\"cfg\": ").append(exportCfgJson(func));
        sb.append("}");
        return sb.toString();
    }

    private void emit(String json) {
        println("===RESULT===" + json);
    }

    private String jsonEscape(String s) {
        if (s == null) {
            return "";
        }
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private String exportFunctionsJson() throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        boolean first = true;
        for (Function func : currentProgram.getFunctionManager().getFunctions(true)) {
            if (!first) sb.append(",");
            first = false;
            sb.append(String.format(
                "{\"address\": \"0x%s\", \"name\": \"%s\", \"size\": %d, \"kind\": \"function\"}",
                func.getEntryPoint().toString(),
                jsonEscape(func.getName()),
                func.getBody().getNumAddresses()
            ));
        }
        sb.append("]");
        return sb.toString();
    }

    private String exportMetadataJson() throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        sb.append("\"schema\": \"ghidra-program-metadata-v1\",");
        sb.append("\"binary\": {");
        sb.append("\"format\": \"").append(jsonEscape(currentProgram.getExecutableFormat())).append("\",");
        sb.append("\"bitness\": ").append(currentProgram.getDefaultPointerSize() * 8).append(",");
        sb.append("\"image_base\": ").append(Long.toUnsignedString(currentProgram.getImageBase().getOffset())).append(",");
        sb.append("\"language_id\": \"").append(jsonEscape(currentProgram.getLanguageID().toString())).append("\",");
        sb.append("\"compiler_spec_id\": \"").append(jsonEscape(currentProgram.getCompilerSpec().getCompilerSpecID().toString())).append("\"");
        sb.append("},");

        sb.append("\"memory_blocks\": [");
        boolean first = true;
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!first) sb.append(",");
            first = false;
            sb.append("{");
            sb.append("\"name\": \"").append(jsonEscape(block.getName())).append("\",");
            sb.append("\"start\": ").append(Long.toUnsignedString(block.getStart().getOffset())).append(",");
            sb.append("\"size\": ").append(block.getSize()).append(",");
            sb.append("\"permissions\": {");
            sb.append("\"read\": ").append(block.isRead()).append(",");
            sb.append("\"write\": ").append(block.isWrite()).append(",");
            sb.append("\"execute\": ").append(block.isExecute());
            sb.append("}}");
        }
        sb.append("],");

        sb.append("\"functions\": [");
        first = true;
        for (Function func : currentProgram.getFunctionManager().getFunctions(true)) {
            if (!first) sb.append(",");
            first = false;
            sb.append("{");
            sb.append("\"entry\": ").append(Long.toUnsignedString(func.getEntryPoint().getOffset())).append(",");
            sb.append("\"name\": \"").append(jsonEscape(func.getName())).append("\",");
            sb.append("\"size\": ").append(func.getBody().getNumAddresses()).append(",");
            sb.append("\"is_import\": ").append(func.isExternal()).append(",");
            sb.append("\"is_thunk\": ").append(func.isThunk());
            sb.append("}");
        }
        sb.append("],");

        sb.append("\"symbols\": [");
        first = true;
        SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbols.hasNext()) {
            Symbol symbol = symbols.next();
            if (symbol.getAddress() == null || !symbol.getAddress().isMemoryAddress()) continue;
            if (!first) sb.append(",");
            first = false;
            sb.append("{");
            sb.append("\"address\": ").append(Long.toUnsignedString(symbol.getAddress().getOffset())).append(",");
            sb.append("\"name\": \"").append(jsonEscape(symbol.getName())).append("\",");
            sb.append("\"kind\": \"").append(jsonEscape(symbol.getSymbolType().toString().toLowerCase())).append("\",");
            sb.append("\"source\": \"").append(jsonEscape(symbol.getSource().toString().toLowerCase())).append("\",");
            sb.append("\"primary\": ").append(symbol.isPrimary());
            sb.append("}");
        }
        sb.append("],");

        sb.append("\"relocations\": [");
        first = true;
        Iterator<Relocation> relocations = currentProgram.getRelocationTable().getRelocations();
        while (relocations.hasNext()) {
            Relocation relocation = relocations.next();
            if (!first) sb.append(",");
            first = false;
            byte[] bytes = relocation.getBytes();
            sb.append("{");
            sb.append("\"address\": ").append(Long.toUnsignedString(relocation.getAddress().getOffset())).append(",");
            sb.append("\"relocation_type\": ").append(relocation.getType()).append(",");
            sb.append("\"size\": ").append(bytes == null ? 0 : bytes.length).append(",");
            String symbolName = relocation.getSymbolName();
            if (symbolName == null) {
                sb.append("\"symbol_name\": null");
            } else {
                sb.append("\"symbol_name\": \"").append(jsonEscape(symbolName)).append("\"");
            }
            sb.append("}");
        }
        sb.append("]");
        sb.append("}");
        return sb.toString();
    }

    private String exportDisasmJson(Function func) throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        boolean first = true;
        InstructionIterator insts = currentProgram.getListing().getInstructions(func.getBody(), true);
        while (insts.hasNext()) {
            Instruction inst = insts.next();
            if (!first) sb.append(",");
            first = false;

            byte[] bytes = inst.getBytes();
            StringBuilder byteStr = new StringBuilder();
            for (byte b : bytes) {
                byteStr.append(String.format("%02x", b & 0xff));
            }

            Address fall = inst.getFallThrough();
            Address[] flows = inst.getFlows();
            String branchTarget = (flows.length > 0) ? "\"0x" + flows[0].toString() + "\"" : "null";
            String operands = jsonEscape(inst.toString());

            sb.append(String.format(
                "{\"address\": \"0x%s\", \"bytes\": \"%s\", \"mnemonic\": \"%s\", \"operands\": \"%s\", \"length\": %d, \"fallthrough\": %s, \"branch_target\": %s}",
                inst.getMinAddress().toString(),
                byteStr.toString(),
                inst.getMnemonicString().toLowerCase(),
                operands,
                inst.getLength(),
                fall != null ? "\"0x" + fall.toString() + "\"" : "null",
                branchTarget
            ));
        }
        sb.append("]");
        return sb.toString();
    }

    private String exportPcodeJson(Function func) throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        boolean first = true;
        int seq = 0;
        InstructionIterator insts = currentProgram.getListing().getInstructions(func.getBody(), true);
        while (insts.hasNext()) {
            Instruction inst = insts.next();
            PcodeOp[] ops = inst.getPcode();
            for (PcodeOp op : ops) {
                if (!first) sb.append(",");
                first = false;

                String outputStr = "null";
                Varnode out = op.getOutput();
                if (out != null) {
                    outputStr = String.format(
                        "{\"space\": \"%s\", \"offset\": \"0x%x\", \"size\": %d}",
                        out.getAddress().getAddressSpace().getName(),
                        out.getAddress().getOffset(),
                        out.getSize()
                    );
                }

                StringBuilder inputsStr = new StringBuilder();
                inputsStr.append("[");
                Varnode[] inputs = op.getInputs();
                for (int i = 0; i < inputs.length; i++) {
                    Varnode in = inputs[i];
                    if (i > 0) inputsStr.append(",");
                    inputsStr.append(String.format(
                        "{\"space\": \"%s\", \"offset\": \"0x%x\", \"size\": %d}",
                        in.getAddress().getAddressSpace().getName(),
                        in.getAddress().getOffset(),
                        in.getSize()
                    ));
                }
                inputsStr.append("]");

                sb.append(String.format(
                    "{\"seq\": %d, \"op\": \"%s\", \"output\": %s, \"inputs\": %s}",
                    seq++,
                    op.getMnemonic(),
                    outputStr,
                    inputsStr.toString()
                ));
            }
        }
        sb.append("]");
        return sb.toString();
    }

    private String exportCfgJson(Function func) throws Exception {
        SimpleBlockModel blockModel = new SimpleBlockModel(currentProgram);
        CodeBlockIterator blocks = blockModel.getCodeBlocksContaining(func.getBody(), monitor);

        StringBuilder blocksJson = new StringBuilder();
        blocksJson.append("[");
        boolean firstBlock = true;

        StringBuilder edgesJson = new StringBuilder();
        edgesJson.append("[");
        boolean firstEdge = true;

        while (blocks.hasNext()) {
            CodeBlock block = blocks.next();
            if (!firstBlock) blocksJson.append(",");
            firstBlock = false;

            // Inclusive last byte of last instruction (Fission adapter promotes
            // terminal_address + insn length to the same encoding).
            blocksJson.append(String.format(
                "{\"start\": \"0x%s\", \"end\": \"0x%s\"}",
                block.getMinAddress().toString(),
                block.getMaxAddress().toString()
            ));

            CodeBlockReferenceIterator dests = block.getDestinations(monitor);
            while (dests.hasNext()) {
                CodeBlockReference ref = dests.next();
                if (!firstEdge) edgesJson.append(",");
                firstEdge = false;
                edgesJson.append(String.format(
                    "{\"source\": \"0x%s\", \"target\": \"0x%s\", \"kind\": \"branch\"}",
                    block.getMinAddress().toString(),
                    ref.getDestinationAddress().toString()
                ));
            }
        }
        blocksJson.append("]");
        edgesJson.append("]");

        return "{\"blocks\": " + blocksJson.toString() + ", \"edges\": " + edgesJson.toString() + "}";
    }

    private String exportAbiJson(Function func) throws Exception {
        String conv = func.getCallingConventionName();
        if (conv == null || conv.isEmpty()) {
            conv = "unknown";
        }
        StringBuilder params = new StringBuilder();
        params.append("[");
        Parameter[] arr = func.getParameters();
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) params.append(",");
            params.append(parameterToJson(arr[i], i));
        }
        params.append("]");

        String retJson = "null";
        Parameter ret = func.getReturn();
        if (ret != null) {
            retJson = parameterToJson(ret, -1);
        }

        return String.format(
            "{\"status\": \"ok\", \"address\": \"0x%s\", \"name\": \"%s\", \"convention\": \"%s\", \"parameters\": %s, \"return\": %s}",
            func.getEntryPoint().toString(),
            jsonEscape(func.getName()),
            jsonEscape(conv),
            params.toString(),
            retJson
        );
    }

    private String parameterToJson(Parameter p, int index) {
        String loc = "unknown";
        int size = 0;
        try {
            size = p.getLength();
            // Prefer Register name (RCX/RAX) over raw register-space offsets ("00000008").
            Register reg = p.getRegister();
            VariableStorage storage = p.getVariableStorage();
            if (reg == null && storage != null && storage.isValid()) {
                reg = storage.getRegister();
            }
            if (reg != null) {
                loc = reg.getName().toLowerCase();
            } else if (storage != null && storage.isValid() && storage.isStackStorage()) {
                loc = String.format("stack+0x%x", storage.getStackOffset());
            } else if (storage != null && storage.isValid() && storage.getFirstVarnode() != null) {
                Varnode vn = storage.getFirstVarnode();
                Register r2 = currentProgram.getRegister(vn.getAddress(), vn.getSize());
                if (r2 == null) {
                    r2 = currentProgram.getRegister(vn.getAddress());
                }
                if (r2 != null) {
                    loc = r2.getName().toLowerCase();
                } else {
                    String space = vn.getAddress().getAddressSpace().getName();
                    if ("register".equalsIgnoreCase(space)) {
                        loc = String.format("reg+0x%x", vn.getOffset());
                    } else if ("stack".equalsIgnoreCase(space)) {
                        loc = String.format("stack+0x%x", vn.getAddress().getOffset());
                    } else {
                        loc = space.toLowerCase() + "+0x" + Long.toHexString(vn.getAddress().getOffset());
                    }
                }
            }
        } catch (Exception e) {
            loc = "unknown";
        }
        String name = p.getName() != null ? p.getName() : ("param_" + index);
        return String.format(
            "{\"index\": %d, \"name\": \"%s\", \"location\": \"%s\", \"size\": %d}",
            index,
            jsonEscape(name),
            jsonEscape(loc.toLowerCase()),
            size
        );
    }

    private String exportTypesJson(Function func) throws Exception {
        StringBuilder params = new StringBuilder();
        params.append("[");
        Parameter[] arr = func.getParameters();
        Set<String> seenStructs = new LinkedHashSet<String>();
        StringBuilder structs = new StringBuilder();
        structs.append("[");
        boolean firstStruct = true;
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) params.append(",");
            DataType dt = arr[i].getDataType();
            String ty = dt != null ? dt.getName() : "undefined";
            params.append(String.format(
                "{\"index\": %d, \"name\": \"%s\", \"type\": \"%s\", \"size\": %d}",
                i,
                jsonEscape(arr[i].getName() != null ? arr[i].getName() : ("param_" + i)),
                jsonEscape(ty),
                arr[i].getLength()
            ));
            String structJson = structureFieldsJson(dt, seenStructs);
            if (structJson != null) {
                if (!firstStruct) structs.append(",");
                firstStruct = false;
                structs.append(structJson);
            }
        }
        params.append("]");
        DataType retDt = func.getReturnType();
        String retName = retDt != null ? retDt.getName() : "undefined";
        int retSize = retDt != null ? retDt.getLength() : 0;
        String retStruct = structureFieldsJson(retDt, seenStructs);
        if (retStruct != null) {
            if (!firstStruct) structs.append(",");
            firstStruct = false;
            structs.append(retStruct);
        }
        // Also collect local variable struct types
        for (var local : func.getLocalVariables()) {
            String sj = structureFieldsJson(local.getDataType(), seenStructs);
            if (sj != null) {
                if (!firstStruct) structs.append(",");
                firstStruct = false;
                structs.append(sj);
            }
        }
        structs.append("]");
        return String.format(
            "{\"status\": \"ok\", \"address\": \"0x%s\", \"name\": \"%s\", \"return_type\": \"%s\", \"return_size\": %d, \"parameters\": %s, \"structs\": %s, \"layout_surface\": \"field_iou\"}",
            func.getEntryPoint().toString(),
            jsonEscape(func.getName()),
            jsonEscape(retName),
            retSize,
            params.toString(),
            structs.toString()
        );
    }

    /** Emit one struct layout as fields[{name,offset,size,type}] or null if not a struct. */
    private String structureFieldsJson(DataType dt, Set<String> seen) {
        if (dt == null) return null;
        DataType base = dt;
        // unwrap pointer / typedef
        try {
            while (base instanceof TypeDef) {
                base = ((TypeDef) base).getDataType();
            }
            if (base instanceof ghidra.program.model.data.Pointer) {
                base = ((ghidra.program.model.data.Pointer) base).getDataType();
                while (base instanceof TypeDef) {
                    base = ((TypeDef) base).getDataType();
                }
            }
        } catch (Exception e) {
            return null;
        }
        if (!(base instanceof Structure)) {
            return null;
        }
        Structure st = (Structure) base;
        String key = st.getName() + ":" + st.getLength();
        if (seen.contains(key)) {
            return null;
        }
        seen.add(key);
        StringBuilder fields = new StringBuilder();
        fields.append("[");
        boolean first = true;
        DataTypeComponent[] comps = st.getDefinedComponents();
        for (int i = 0; i < comps.length; i++) {
            DataTypeComponent c = comps[i];
            if (!first) fields.append(",");
            first = false;
            String fname = c.getFieldName() != null ? c.getFieldName() : ("field_" + i);
            DataType fdt = c.getDataType();
            String fty = fdt != null ? fdt.getName() : "undefined";
            fields.append(String.format(
                "{\"name\": \"%s\", \"offset\": %d, \"size\": %d, \"type\": \"%s\"}",
                jsonEscape(fname),
                c.getOffset(),
                c.getLength(),
                jsonEscape(fty)
            ));
        }
        fields.append("]");
        return String.format(
            "{\"name\": \"%s\", \"size\": %d, \"fields\": %s}",
            jsonEscape(st.getName()),
            st.getLength(),
            fields.toString()
        );
    }

    private String exportCallgraphJson(Function func) throws Exception {
        Set<String> callees = new LinkedHashSet<String>();
        InstructionIterator insts = currentProgram.getListing().getInstructions(func.getBody(), true);
        while (insts.hasNext()) {
            Instruction inst = insts.next();
            Reference[] refs = inst.getReferencesFrom();
            for (int i = 0; i < refs.length; i++) {
                Reference ref = refs[i];
                if (ref == null) continue;
                RefType rt = ref.getReferenceType();
                if (rt == null || !rt.isCall()) continue;
                Address to = ref.getToAddress();
                Function target = currentProgram.getFunctionManager().getFunctionAt(to);
                if (target == null) {
                    target = currentProgram.getFunctionManager().getFunctionContaining(to);
                }
                if (target != null) {
                    callees.add(String.format("0x%s", target.getEntryPoint().toString()));
                } else if (to != null) {
                    callees.add(String.format("0x%s", to.toString()));
                }
            }
        }
        StringBuilder edges = new StringBuilder();
        edges.append("[");
        boolean first = true;
        String src = "0x" + func.getEntryPoint().toString();
        for (String tgt : callees) {
            if (!first) edges.append(",");
            first = false;
            edges.append(String.format(
                "{\"source\": \"%s\", \"target\": \"%s\", \"kind\": \"call\"}",
                src, tgt
            ));
        }
        edges.append("]");
        return String.format(
            "{\"status\": \"ok\", \"address\": \"%s\", \"callees\": %s, \"edges\": %s, \"callee_count\": %d}",
            src,
            toJsonStringArray(callees),
            edges.toString(),
            callees.size()
        );
    }

    private String toJsonStringArray(Set<String> items) {
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        boolean first = true;
        for (String s : items) {
            if (!first) sb.append(",");
            first = false;
            sb.append("\"").append(jsonEscape(s)).append("\"");
        }
        sb.append("]");
        return sb.toString();
    }

    private String exportStringsJson(Function func) throws Exception {
        Set<String> strings = new LinkedHashSet<String>();
        InstructionIterator insts = currentProgram.getListing().getInstructions(func.getBody(), true);
        while (insts.hasNext()) {
            Instruction inst = insts.next();
            Reference[] refs = inst.getReferencesFrom();
            for (Reference ref : refs) {
                if (ref == null || ref.getToAddress() == null) continue;
                Data data = currentProgram.getListing().getDataAt(ref.getToAddress());
                if (data == null) {
                    data = currentProgram.getListing().getDataContaining(ref.getToAddress());
                }
                if (data != null && data.hasStringValue()) {
                    Object val = data.getValue();
                    if (val != null) {
                        String text = String.valueOf(val).trim();
                        if (!text.isEmpty() && text.length() <= 256) {
                            strings.add(text);
                        }
                    }
                }
            }
        }
        return String.format(
            "{\"status\": \"ok\", \"address\": \"0x%s\", \"strings\": %s, \"count\": %d}",
            func.getEntryPoint().toString(),
            toJsonStringArray(strings),
            strings.size()
        );
    }

    private String exportDataflowJson(Function func) throws Exception {
        // Compact sinks: RETURN outputs + STORE destinations (space+offset keys).
        Set<String> returns = new LinkedHashSet<String>();
        Set<String> stores = new LinkedHashSet<String>();
        InstructionIterator insts = currentProgram.getListing().getInstructions(func.getBody(), true);
        while (insts.hasNext()) {
            Instruction inst = insts.next();
            PcodeOp[] ops = inst.getPcode();
            for (PcodeOp op : ops) {
                int opc = op.getOpcode();
                if (opc == PcodeOp.RETURN) {
                    if (op.getNumInputs() > 1 && op.getInput(1) != null) {
                        returns.add(varnodeKey(op.getInput(1)));
                    } else {
                        returns.add("void");
                    }
                } else if (opc == PcodeOp.STORE) {
                    if (op.getNumInputs() >= 3) {
                        stores.add(varnodeKey(op.getInput(1)) + "<-" + varnodeKey(op.getInput(2)));
                    }
                }
            }
        }
        return String.format(
            "{\"status\": \"ok\", \"address\": \"0x%s\", \"return_sinks\": %s, \"store_sinks\": %s}",
            func.getEntryPoint().toString(),
            toJsonStringArray(returns),
            toJsonStringArray(stores)
        );
    }

    private String varnodeKey(Varnode vn) {
        if (vn == null) return "null";
        try {
            String space = vn.getAddress().getAddressSpace().getName();
            return space + "+0x" + Long.toHexString(vn.getOffset()) + ":" + vn.getSize();
        } catch (Exception e) {
            return "unknown";
        }
    }

    private String exportSehJson(Function func) throws Exception {
        boolean isThunk = func.isThunk();
        boolean noReturn = func.hasNoReturn();
        String conv = func.getCallingConventionName();
        if (conv == null) conv = "unknown";
        int ehCount = 0;
        try {
            var syms = currentProgram.getSymbolTable().getSymbolIterator(true);
            while (syms.hasNext()) {
                String n = syms.next().getName().toLowerCase();
                if (n.contains("exception") || n.contains("__c_specific_handler")
                        || n.contains("_unwind") || n.contains("gs_handler")) {
                    ehCount++;
                }
            }
        } catch (Exception ignored) {
        }
        // Map PE exception blocks if the program exposes them via memory blocks named .pdata
        long imageBase = currentProgram.getImageBase().getOffset();
        long entry = func.getEntryPoint().getOffset();
        long rva = entry - imageBase;
        boolean hasUnwind = false;
        long beginRva = -1, endRva = -1, unwindRva = -1;
        try {
            var block = currentProgram.getMemory().getBlock(".pdata");
            if (block != null) {
                Address start = block.getStart();
                long size = block.getSize();
                // Each RUNTIME_FUNCTION is 12 bytes: begin, end, unwind (RVA dwords)
                for (long off = 0; off + 12 <= size; off += 12) {
                    Address a = start.add(off);
                    // Read little-endian dwords from memory
                    byte[] buf = new byte[12];
                    currentProgram.getMemory().getBytes(a, buf);
                    int b0 = (buf[0] & 0xff) | ((buf[1] & 0xff) << 8) | ((buf[2] & 0xff) << 16) | ((buf[3] & 0xff) << 24);
                    int e0 = (buf[4] & 0xff) | ((buf[5] & 0xff) << 8) | ((buf[6] & 0xff) << 16) | ((buf[7] & 0xff) << 24);
                    int u0 = (buf[8] & 0xff) | ((buf[9] & 0xff) << 8) | ((buf[10] & 0xff) << 16) | ((buf[11] & 0xff) << 24);
                    long br = b0 & 0xffffffffL;
                    long er = e0 & 0xffffffffL;
                    if (br <= rva && rva < er) {
                        hasUnwind = true;
                        beginRva = br;
                        endRva = er;
                        unwindRva = u0 & 0xffffffffL;
                        break;
                    }
                }
            }
        } catch (Exception ignored) {
        }
        String covering = "null";
        if (hasUnwind) {
            covering = String.format(
                "{\"begin_rva\": %d, \"end_rva\": %d, \"unwind_info_rva\": %d, \"begin_va\": \"0x%x\", \"end_va\": \"0x%x\"}",
                beginRva, endRva, unwindRva, imageBase + beginRva, imageBase + endRva
            );
        }
        return String.format(
            "{\"status\": \"ok\", \"address\": \"0x%s\", \"is_thunk\": %s, \"no_return\": %s, \"convention\": \"%s\", \"program_eh_symbol_count\": %d, \"has_unwind\": %s, \"rva\": %d, \"covering\": %s, \"seh_surface\": \"runtime_function\"}",
            func.getEntryPoint().toString(),
            isThunk ? "true" : "false",
            noReturn ? "true" : "false",
            jsonEscape(conv),
            ehCount,
            hasUnwind ? "true" : "false",
            rva,
            covering
        );
    }
}
