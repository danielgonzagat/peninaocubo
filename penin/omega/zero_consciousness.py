"""Zero-Consciousness Proof (SPI proxy)"""
def spi_proxy(ece:float, randomness:float, introspection_leak:float)->float:
    return 0.5*ece + 0.4*randomness + 0.1*introspection_leak

def assert_zero_consciousness(spi:float, tau:float=0.05)->bool:
    return spi <= tau