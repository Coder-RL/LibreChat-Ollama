-- Find the maximum supported vector dimensions that work with your pgvector installation
BEGIN;

-- Test various dimensions to find the maximum that works for both creation and insertion
DO $$
DECLARE
    dim_works BOOLEAN;
    max_working_dim INTEGER := 0;
    curr_test_dim INTEGER;
    datatype TEXT;
    dimension INTEGER;
BEGIN
    -- First test with powers of 2 to find the approximate range
    FOR power IN 0..12 LOOP  -- Test up to 2^12 = 4096
        curr_test_dim := POWER(2, power)::INTEGER;
        
        -- Try creating a table with this dimension
        dim_works := TRUE;
        BEGIN
            EXECUTE 'CREATE TEMP TABLE vector_test_' || curr_test_dim || ' (v vector(' || curr_test_dim || '))';
            
            -- Check the actual dimension
            EXECUTE 'SELECT pg_catalog.format_type(atttypid, atttypmod) AS datatype, 
                           atttypmod-4 AS dimension
                     FROM pg_attribute
                     JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
                     WHERE relname = ''vector_test_' || curr_test_dim || ''' 
                     AND attname = ''v'''
            INTO datatype, dimension;
            
            -- Try inserting a vector
            BEGIN
                -- Create a short vector with just first 3 values
                EXECUTE 'INSERT INTO vector_test_' || curr_test_dim || ' VALUES (''[0.1, 0.2, 0.3]'')';
                
                -- Verify successful insertion
                EXECUTE 'SELECT COUNT(*) FROM vector_test_' || curr_test_dim INTO dim_works;
                dim_works := dim_works > 0;
                
                IF dim_works THEN
                    max_working_dim := curr_test_dim;
                    RAISE NOTICE 'Dimension % works: datatype=%, actual dimension=%', 
                        curr_test_dim, datatype, dimension;
                END IF;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Insertion failed for dimension %: %', curr_test_dim, SQLERRM;
                dim_works := FALSE;
            END;
            
            -- Clean up
            EXECUTE 'DROP TABLE vector_test_' || curr_test_dim;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Creation failed for dimension %: %', curr_test_dim, SQLERRM;
            dim_works := FALSE;
        END;
    END LOOP;
    
    RAISE NOTICE '----- Maximum power of 2 working dimension: % -----', max_working_dim;
    
    -- Now test specific dimensions around the highest working power of 2
    -- This helps find the exact maximum
    IF max_working_dim > 0 THEN
        DECLARE
            lower_bound INTEGER := GREATEST(max_working_dim / 2, 1);
            upper_bound INTEGER := max_working_dim * 2;
            step INTEGER := GREATEST(max_working_dim / 8, 1);
        BEGIN
            FOR curr_test_dim IN SELECT * FROM generate_series(lower_bound, upper_bound, step) LOOP
                -- Skip the power of 2 we already tested
                IF curr_test_dim = max_working_dim THEN
                    CONTINUE;
                END IF;
                
                dim_works := TRUE;
                BEGIN
                    EXECUTE 'CREATE TEMP TABLE vector_test_' || curr_test_dim || ' (v vector(' || curr_test_dim || '))';
                    
                    -- Try inserting a vector
                    BEGIN
                        EXECUTE 'INSERT INTO vector_test_' || curr_test_dim || ' VALUES (''[0.1, 0.2, 0.3]'')';
                        
                        -- Verify successful insertion
                        EXECUTE 'SELECT COUNT(*) FROM vector_test_' || curr_test_dim INTO dim_works;
                        dim_works := dim_works > 0;
                        
                        IF dim_works AND curr_test_dim > max_working_dim THEN
                            max_working_dim := curr_test_dim;
                            RAISE NOTICE 'Higher dimension % works!', curr_test_dim;
                        END IF;
                    EXCEPTION WHEN OTHERS THEN
                        RAISE NOTICE 'Insertion failed for dimension %: %', curr_test_dim, SQLERRM;
                        dim_works := FALSE;
                    END;
                    
                    -- Clean up
                    EXECUTE 'DROP TABLE vector_test_' || curr_test_dim;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Creation failed for dimension %: %', curr_test_dim, SQLERRM;
                    dim_works := FALSE;
                END;
            END LOOP;
        END;
    END IF;
    
    RAISE NOTICE '====================================================';
    RAISE NOTICE 'MAXIMUM WORKING DIMENSION: %', max_working_dim;
    RAISE NOTICE '====================================================';
END $$;

ROLLBACK;