{
	inputs = {
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
	};

	outputs = { nixpkgs, ... }:
    let
    	pkgs = import nixpkgs {
    		config.allowUnfree = true;
        	system = "x86_64-linux";
	    };
    in
    {
    	devShells.x86_64-linux.default = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [
                python312
                stdenv.cc.cc.lib
            ];
            shellHook = ''
                export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
                export EXTRA_CCFLAGS="-I/usr/include"
            '';
        };
    };
}
