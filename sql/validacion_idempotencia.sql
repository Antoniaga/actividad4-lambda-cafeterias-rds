-- Conteo total de registros
SELECT COUNT(*)
FROM cafeterias_teusaquillo;

-- Verificación de unicidad después de re-ejecutar Lambda
SELECT
    COUNT(*) AS total_registros,
    COUNT(DISTINCT fsq_place_id) AS ids_unicos
FROM cafeterias_teusaquillo;